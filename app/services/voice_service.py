"""VoiceService: the complete voice lifecycle (create, edit, samples, revoke, delete)."""

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.consent_status import ConsentStatus
from app.constants.status import Status
from app.exceptions import ConsentError, NotFoundError, VoiceError
from app.models import Voice, VoiceSample
from app.services.consent_service import consent_service
from app.utils.database import deleted_result, read_session, serialize, transaction
from app.utils.files import remove_file, remove_tree, subdir
from app.utils.logger import logger
from app.utils.model import VoiceRef
from app.utils.validation import require_name

PRESET = "preset"
CLONE = "clone"


class VoiceService:
    # ------------------------------------------------------------ helpers

    def to_dict(self, voice: Voice, with_samples: bool = False) -> dict:
        data = serialize(voice, exclude=("storage_dir",))
        data["consent_status_label"] = ConsentStatus.label(voice.consent_status)
        data["pitch_hz"] = (voice.profile or {}).get("pitch_hz")
        data.pop("profile", None)
        if with_samples:
            data["samples"] = [
                serialize(s, exclude=("sha256",)) for s in voice.samples if s.status == Status.ACTIVE.code
            ]
        return data

    def _get(self, session: Session, voices_id: int, include_revoked: bool = False) -> Voice:
        voice = session.get(Voice, voices_id)
        if voice is None or voice.status == Status.DELETED.code:
            raise NotFoundError(f"Voice {voices_id} not found", field="voices_id")
        if voice.consent_status == ConsentStatus.REVOKED.code and not include_revoked:
            raise VoiceError(f"Voice '{voice.name}' has been revoked", field="voices_id")
        return voice

    def storage_dir(self, voices_id: int) -> Path:
        return subdir("voices", voices_id)

    # ------------------------------------------------------------ create / read

    def create_in(self, session: Session, name: str, *, source: str = PRESET, **fields) -> Voice:
        """Insert a voice inside the caller's transaction (used by CloneService)."""
        voice = Voice(name=require_name(name), source=source, **fields)
        session.add(voice)
        session.flush()
        if source == CLONE:
            voice.storage_dir = str(self.storage_dir(voice.voices_id))
        return voice

    def create(self, name: str, *, engine_voice: str | None = None, model_key: str | None = None,
               language: str = "en", description: str = "", users_id: int | None = None) -> dict:
        """Create a preset voice (an engine's built-in speaker). Cloned voices go through CloneService."""
        with transaction() as session:
            voice = self.create_in(
                session, name, source=PRESET, engine_voice=engine_voice, model_key=model_key,
                language=language, description=description, users_id=users_id,
                consent_status=ConsentStatus.NOT_REQUIRED.code,
            )
            logger.info(f"Created preset voice {voice.voices_id}")
            return self.to_dict(voice)

    def get(self, voices_id: int, with_samples: bool = True) -> dict:
        with read_session() as session:
            return self.to_dict(self._get(session, voices_id, include_revoked=True), with_samples=with_samples)

    def list_voices(self, include_revoked: bool = False, users_id: int | None = None) -> list[dict]:
        with read_session() as session:
            query = select(Voice).where(Voice.status != Status.DELETED.code)
            if not include_revoked:
                query = query.where(Voice.consent_status != ConsentStatus.REVOKED.code)
            if users_id is not None:
                query = query.where(Voice.users_id == users_id)
            return [self.to_dict(v) for v in session.scalars(query.order_by(Voice.updated_at.desc()))]

    # ------------------------------------------------------------ update

    def update(self, voices_id: int, **fields) -> dict:
        allowed = {"name", "description", "language", "model_key", "engine_voice", "preview_audios_id"}
        unknown = set(fields) - allowed
        if unknown:
            raise VoiceError(f"Cannot update: {', '.join(sorted(unknown))}")
        with transaction() as session:
            voice = self._get(session, voices_id)
            for key, value in fields.items():
                if value is None:
                    continue
                setattr(voice, key, require_name(value) if key == "name" else value)
            return self.to_dict(voice)

    def save(self, voices_id: int | None = None, status: int | None = None, **fields) -> dict:
        """One entry point: create a preset voice (no id), delete (status = Deleted) or update.

        Cloned voices are created through CloneService because they need samples and consent.
        """
        if voices_id is None:
            return self.create(**fields)
        if status == Status.DELETED.code:
            self.delete(voices_id)
            return deleted_result("voices_id", voices_id)
        return self.update(voices_id, **fields)

    def rename(self, voices_id: int, name: str) -> dict:
        return self.update(voices_id, name=name)

    # ------------------------------------------------------------ samples

    def attach_sample(self, voices_id: int, path: str | Path) -> dict:
        """Add another reference recording to an existing cloned voice."""
        from app.services.clone_service import clone_service

        with read_session() as session:
            voice = self._get(session, voices_id)
            if voice.source != CLONE:
                raise VoiceError("Samples can only be added to cloned voices")
            consent_service.require_active(session, voices_id)
        prepared = clone_service.prepare_sample(path, self.storage_dir(voices_id))
        try:
            with transaction() as session:
                voice = self._get(session, voices_id)
                voice.samples.append(VoiceSample(**prepared["record"]))
                self._refresh_counts(voice)
                voice.profile = clone_service.build_profile(self._active_sample_paths(voice))
                session.flush()
                return self.to_dict(voice, with_samples=True)
        except Exception:
            remove_file(prepared["record"]["path"])
            raise

    def remove_sample(self, voice_samples_id: int) -> dict:
        with transaction() as session:
            sample = session.get(VoiceSample, voice_samples_id)
            if sample is None:
                raise NotFoundError(f"Sample {voice_samples_id} not found", field="voice_samples_id")
            voice = self._get(session, sample.voices_id)
            active = [s for s in voice.samples if s.status == Status.ACTIVE.code]
            if len(active) <= 1:
                raise VoiceError("A cloned voice needs at least one sample. Delete the voice instead.")
            from app.services.clone_service import clone_service

            path = sample.path
            voice.samples.remove(sample)
            self._refresh_counts(voice)
            voice.profile = clone_service.build_profile(self._active_sample_paths(voice))
            voices_id = voice.voices_id
        remove_file(path)
        return self.get(voices_id)

    def _active_sample_paths(self, voice: Voice) -> list[str]:
        return [s.path for s in voice.samples if s.status == Status.ACTIVE.code]

    def _refresh_counts(self, voice: Voice) -> None:
        voice.sample_count = len(self._active_sample_paths(voice))

    # ------------------------------------------------------------ revoke / delete

    def revoke(self, voices_id: int) -> dict:
        """Withdraw consent: deletes samples and profile; the row stays Inactive with consent Revoked."""
        with transaction() as session:
            voice = self._get(session, voices_id, include_revoked=True)
            storage = voice.storage_dir
            for sample in list(voice.samples):
                session.delete(sample)
            consent_service.revoke(session, voices_id)
            voice.status = Status.INACTIVE.code
            voice.consent_status = ConsentStatus.REVOKED.code
            voice.profile = {}
            voice.sample_count = 0
            result = self.to_dict(voice)
        remove_tree(storage)
        logger.info(f"Voice {voices_id} revoked and its data deleted")
        return result

    def delete(self, voices_id: int) -> None:
        """Remove the voice, its samples, consent records and files completely."""
        with transaction() as session:
            voice = self._get(session, voices_id, include_revoked=True)
            storage = voice.storage_dir
            session.delete(voice)
        remove_tree(storage)
        logger.info(f"Voice {voices_id} deleted")

    # ------------------------------------------------------------ synthesis support

    def validate(self, voices_id: int) -> dict:
        """Check a voice can be used for generation; returns its dict."""
        with read_session() as session:
            voice = self._get(session, voices_id)
            if voice.source == CLONE:
                consent_service.require_active(session, voices_id)
                if not voice.sample_count:
                    raise VoiceError(f"Voice '{voice.name}' has no samples")
            return self.to_dict(voice)

    def voice_ref(self, voices_id: int) -> tuple[VoiceRef, dict]:
        with read_session() as session:
            voice = self._get(session, voices_id)
            if voice.source == CLONE and not consent_service.has_active(session, voices_id):
                raise ConsentError(f"Voice '{voice.name}' has no active consent")
            ref = VoiceRef(
                sample_paths=[s.path for s in voice.samples if s.status == Status.ACTIVE.code],
                language=voice.language,
                pitch_hz=float((voice.profile or {}).get("pitch_hz") or 0.0),
                engine_voice=voice.engine_voice,
            )
            return ref, self.to_dict(voice)

    def export_metadata(self, voices_id: int) -> dict:
        data = self.get(voices_id, with_samples=True)
        for sample in data.get("samples", []):
            sample["file"] = Path(sample.pop("path")).name
        data["consents"] = consent_service.history(voices_id)
        return data


voice_service = VoiceService()
