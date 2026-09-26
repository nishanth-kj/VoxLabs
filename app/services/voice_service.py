"""VoiceService: the complete voice lifecycle (create, edit, samples, revoke, delete)."""

from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.audio import STYLE_PRESETS
from app.constants.consent_status import ConsentStatus
from app.constants.models import DEFAULT_TTS_MODEL
from app.constants.status import Status
from app.constants.voices import EDGE_VOICES, KOKORO_VOICES, PIPER_VOICE
from app.exceptions import ConsentError, NotFoundError, VoiceError, service_error
from app.models import Voice, VoiceSample
from app.models.request import VoiceRequest
from app.services.consent_service import consent_service
from app.services.system_service import system_service
from app.utils.database import deleted_result, read_session, serialize, transaction
from app.utils.files import remove_file, remove_tree, save_upload, subdir
from app.utils.logger import logger
from app.utils.model import VoiceRef
from app.utils.validation import Validation

PRESET = "preset"
CLONE = "clone"
DELIVERY_DEFAULTS = {"speed": 1.0, "pitch": 1.0, "energy": 1.0, "emotion": "neutral", "style": "default"}


class VoiceService:
    # ------------------------------------------------------------ helpers

    def to_dict(self, voice: Voice, with_samples: bool = False) -> dict:
        data = serialize(voice, exclude=("storage_dir",))
        data["consent_status_label"] = ConsentStatus.label(voice.consent_status)
        data["pitch_hz"] = (voice.profile or {}).get("pitch_hz")
        data["delivery"] = self.normalize_delivery(data.get("delivery"))
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
        voice = Voice(name=Validation.require_name(name), source=source, **fields)
        session.add(voice)
        session.flush()
        if source == CLONE:
            voice.storage_dir = str(self.storage_dir(voice.voices_id))
        return voice

    def ensure_builtin_voices(self) -> int:
        """Create the Piper, Kokoro and Edge preset voices once, and pick Piper Lessac as the default."""
        try:
            if system_service.get_setting("builtin_voices_seeded"):
                return 0
            specs = [{
                "name": PIPER_VOICE["name"],
                "language": PIPER_VOICE["language"],
                "description": PIPER_VOICE["description"],
                "model_key": DEFAULT_TTS_MODEL,
                "engine_voice": None,
            }]
            specs.extend(
                {"name": voice["name"], "language": voice["language"], "description": voice["description"],
                 "model_key": "kokoro-82m", "engine_voice": voice["id"]}
                for voice in KOKORO_VOICES
            )
            specs.extend(
                {"name": voice["name"], "language": voice["language"], "description": voice["description"],
                 "model_key": "edge-neural", "engine_voice": voice["id"]}
                for voice in EDGE_VOICES
            )
            added = 0
            with transaction() as session:
                existing = {
                    (row.model_key, row.engine_voice)
                    for row in session.scalars(select(Voice).where(Voice.status != Status.DELETED.code))
                }
                for spec in specs:
                    if (spec["model_key"], spec["engine_voice"]) in existing:
                        continue
                    self.create_in(
                        session, spec["name"], source=PRESET, engine_voice=spec["engine_voice"],
                        model_key=spec["model_key"], language=spec["language"], description=spec["description"],
                        consent_status=ConsentStatus.NOT_REQUIRED.code,
                    )
                    added += 1
            if system_service.get_setting("default_voices_id") is None:
                with read_session() as session:
                    piper = session.scalar(
                        select(Voice).where(
                            Voice.model_key == DEFAULT_TTS_MODEL,
                            Voice.engine_voice.is_(None),
                            Voice.status != Status.DELETED.code,
                        )
                    )
                if piper is not None:
                    system_service.update_settings(default_voices_id=piper.voices_id)
            system_service.update_settings(builtin_voices_seeded=True)
            logger.info(f"Added {added} built-in voices")
            return added
        except Exception as exc:
            raise service_error(exc, "voice_service.ensure_builtin_voices")

    def create(self, name: str | None, *, engine_voice: str | None = None, model_key: str | None = None,
               language: str | None = "en", description: str | None = "", users_id: int | None = None) -> dict:
        """Create a preset voice (an engine's built-in speaker). Cloned voices go through CloneService."""
        try:
            with transaction() as session:
                voice = self.create_in(
                    session, Validation.require_name(name), source=PRESET, engine_voice=engine_voice,
                    model_key=model_key, language=language or "en", description=description or "",
                    users_id=users_id, consent_status=ConsentStatus.NOT_REQUIRED.code,
                )
                logger.info(f"Created preset voice {voice.voices_id}")
                return self.to_dict(voice)
        except Exception as exc:
            raise service_error(exc, "voice_service.create")

    def get(self, voices_id: int, with_samples: bool = True) -> dict:
        try:
            with read_session() as session:
                return self.to_dict(self._get(session, voices_id, include_revoked=True), with_samples=with_samples)
        except Exception as exc:
            raise service_error(exc, "voice_service.get")

    def list_voices(self, include_revoked: bool = False, users_id: int | None = None) -> list[dict]:
        try:
            with read_session() as session:
                query = select(Voice).where(Voice.status != Status.DELETED.code)
                if not include_revoked:
                    query = query.where(Voice.consent_status != ConsentStatus.REVOKED.code)
                if users_id is not None:
                    query = query.where(Voice.users_id == users_id)
                return [self.to_dict(v) for v in session.scalars(query.order_by(Voice.updated_at.desc()))]
        except Exception as exc:
            raise service_error(exc, "voice_service.list_voices")

    # ------------------------------------------------------------ update

    def normalize_delivery(self, raw: dict | None) -> dict:
        """Fill any missing speaking settings so callers always see a complete delivery."""
        delivery = dict(DELIVERY_DEFAULTS)
        if isinstance(raw, dict):
            delivery.update({key: raw[key] for key in DELIVERY_DEFAULTS if raw.get(key) is not None})
        return delivery

    def clean_delivery(self, raw: dict | None) -> dict:
        if not isinstance(raw, dict):
            raise VoiceError("Delivery settings must be an object", field="delivery")
        cleaned: dict = {}
        if raw.get("speed") is not None:
            cleaned["speed"] = Validation.in_range(float(raw["speed"]), 0.5, 2.0, "speed", 1.0)
        if raw.get("pitch") is not None:
            cleaned["pitch"] = Validation.in_range(float(raw["pitch"]), 0.5, 2.0, "pitch", 1.0)
        if raw.get("energy") is not None:
            cleaned["energy"] = Validation.in_range(float(raw["energy"]), 0.1, 2.0, "energy", 1.0)
        if raw.get("emotion") is not None:
            cleaned["emotion"] = Validation.require_emotion(str(raw["emotion"]))
        if raw.get("style") is not None:
            cleaned["style"] = Validation.require_choice(str(raw["style"]), STYLE_PRESETS, "style")
        return cleaned

    def apply_delivery(self, voice: dict | None, params: dict) -> dict:
        """Use the voice editor's settings wherever the caller left a speaking field unset."""
        delivery = (voice or {}).get("delivery") or {}
        merged = dict(params)
        for key in DELIVERY_DEFAULTS:
            if merged.get(key) is None and delivery.get(key) is not None:
                merged[key] = delivery[key]
        return merged

    def update(self, voices_id: int, **fields) -> dict:
        try:
            allowed = {"name", "description", "language", "model_key", "engine_voice", "delivery",
                       "preview_audios_id"}
            unknown = set(fields) - allowed
            if unknown:
                raise VoiceError(f"Cannot update: {', '.join(sorted(unknown))}")
            with transaction() as session:
                voice = self._get(session, voices_id)
                if "delivery" in fields and fields["delivery"] is not None:
                    fields["delivery"] = {**(voice.delivery or {}), **self.clean_delivery(fields["delivery"])}
                for key, value in fields.items():
                    if value is None and key not in {"model_key", "engine_voice"}:
                        continue
                    if key == "name":
                        value = Validation.require_name(value)
                    setattr(voice, key, value)
                logger.info(f"Updated voice {voices_id}: {', '.join(sorted(fields))}")
                return self.to_dict(voice)
        except Exception as exc:
            raise service_error(exc, "voice_service.update")

    def save(self, body: VoiceRequest) -> dict:
        """One entry point: create a preset voice (no id), delete (status = Deleted) or update.

        Cloned voices are created through CloneService because they need samples and consent.
        """
        try:
            if body.voices_id is None:
                return self.create(body.name, engine_voice=body.engine_voice, model_key=body.model_key,
                                   language=body.language, description=body.description, users_id=body.users_id)
            if body.status == Status.DELETED.code:
                self.delete(body.voices_id)
                return deleted_result("voices_id", body.voices_id)
            return self.update(body.voices_id, **body.model_dump(exclude_unset=True, exclude={"voices_id", "status"}))
        except Exception as exc:
            raise service_error(exc, "voice_service.save")

    def rename(self, voices_id: int, name: str) -> dict:
        return self.update(voices_id, name=name)

    # ------------------------------------------------------------ samples

    def attach_sample(self, voices_id: int, path: str | Path) -> dict:
        """Add another reference recording to an existing cloned voice."""
        from app.services.clone_service import clone_service

        try:
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
                    result = self.to_dict(voice, with_samples=True)
            except Exception:
                remove_file(prepared["record"]["path"])
                raise
            logger.info(f"Added a sample to voice {voices_id}")
            return result
        except Exception as exc:
            raise service_error(exc, "voice_service.attach_sample")

    def attach_upload(self, voices_id: int, upload: UploadFile) -> dict:
        """attach_sample for an uploaded file; the temporary upload is always removed."""
        path = None
        try:
            path = save_upload(upload)
            return self.attach_sample(voices_id, path)
        except Exception as exc:
            raise service_error(exc, "voice_service.attach_upload")
        finally:
            remove_file(path)

    def remove_sample(self, voice_samples_id: int) -> dict:
        from app.services.clone_service import clone_service

        try:
            with transaction() as session:
                sample = session.get(VoiceSample, voice_samples_id)
                if sample is None:
                    raise NotFoundError(f"Sample {voice_samples_id} not found", field="voice_samples_id")
                voice = self._get(session, sample.voices_id)
                active = [s for s in voice.samples if s.status == Status.ACTIVE.code]
                if len(active) <= 1:
                    raise VoiceError("A cloned voice needs at least one sample. Delete the voice instead.")
                path = sample.path
                voice.samples.remove(sample)
                self._refresh_counts(voice)
                voice.profile = clone_service.build_profile(self._active_sample_paths(voice))
                voices_id = voice.voices_id
            remove_file(path)
            logger.info(f"Removed sample {voice_samples_id} from voice {voices_id}")
            return self.get(voices_id)
        except Exception as exc:
            raise service_error(exc, "voice_service.remove_sample")

    def _active_sample_paths(self, voice: Voice) -> list[str]:
        return [s.path for s in voice.samples if s.status == Status.ACTIVE.code]

    def _refresh_counts(self, voice: Voice) -> None:
        voice.sample_count = len(self._active_sample_paths(voice))

    # ------------------------------------------------------------ revoke / delete

    def revoke(self, voices_id: int) -> dict:
        """Withdraw consent: deletes samples and profile; the row stays Inactive with consent Revoked."""
        try:
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
        except Exception as exc:
            raise service_error(exc, "voice_service.revoke")

    def delete(self, voices_id: int) -> None:
        """Remove the voice, its samples, consent records and files completely."""
        try:
            with transaction() as session:
                voice = self._get(session, voices_id, include_revoked=True)
                storage = voice.storage_dir
                session.delete(voice)
            remove_tree(storage)
            logger.info(f"Voice {voices_id} deleted")
        except Exception as exc:
            raise service_error(exc, "voice_service.delete")

    # ------------------------------------------------------------ synthesis support

    def validate(self, voices_id: int) -> dict:
        """Check a voice can be used for generation; returns its dict."""
        try:
            with read_session() as session:
                voice = self._get(session, voices_id)
                if voice.source == CLONE:
                    consent_service.require_active(session, voices_id)
                    if not voice.sample_count:
                        raise VoiceError(f"Voice '{voice.name}' has no samples")
                return self.to_dict(voice)
        except Exception as exc:
            raise service_error(exc, "voice_service.validate")

    def voice_ref(self, voices_id: int) -> tuple[VoiceRef, dict]:
        try:
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
        except Exception as exc:
            raise service_error(exc, "voice_service.voice_ref")

    def export_metadata(self, voices_id: int) -> dict:
        try:
            data = self.get(voices_id, with_samples=True)
            for sample in data.get("samples", []):
                sample["file"] = Path(sample.pop("path")).name
            data["consents"] = consent_service.history(voices_id)
            return data
        except Exception as exc:
            raise service_error(exc, "voice_service.export_metadata")


voice_service = VoiceService()
