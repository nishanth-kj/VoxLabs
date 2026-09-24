"""CloneService: turn consented voice samples into a reusable voice.

Flow: validate files → check consent → select cloning model → analyze and
prepare samples (trim, normalize, resample) → build voice profile → create
voice + consent + samples in a single transaction.
"""

import uuid
from collections.abc import Callable
from pathlib import Path

import numpy as np

from app.constants.audio import CLONE_MAX_SECONDS, CLONE_MIN_SAMPLE_RATE, CLONE_MIN_SECONDS, CLONE_TARGET_SAMPLE_RATE
from app.constants.jobs import JobType
from app.constants.models import ModelType
from app.constants.consent_status import ConsentStatus
from app.constants.status import Status
from app.exceptions import ModelError, ValidationError, VoiceError
from app.models import VoiceSample
from app.services.audio_service import audio_service
from app.services.consent_service import consent_service
from app.services.job_service import job_service
from app.services.model_service import model_service
from app.services.system_service import system_service
from app.services.voice_service import CLONE, voice_service
from app.utils import audio as au
from app.utils.database import transaction
from app.utils.files import remove_file, remove_tree, subdir, unique_path
from app.utils.hashing import sha256_file
from app.utils.logger import logger
from app.utils.model import extract_voice_profile
from app.utils.validation import require_audio_file, require_name

PREVIEW_TEXT = "Hello! This is a preview of my VoxLabs voice. Generated audio is labeled as AI generated."


class CloneService:
    def analyze_sample(self, path: str | Path) -> dict:
        """Quality report plus blocking `errors` for the Clone page's analysis step."""
        analysis = audio_service.analyze(path)
        errors = []
        if analysis["duration"] < 1.0:
            errors.append("Sample is shorter than 1 second")
        if analysis["duration"] > CLONE_MAX_SECONDS:
            errors.append(f"Sample is longer than {int(CLONE_MAX_SECONDS)} seconds — trim it first")
        if analysis["sample_rate"] < CLONE_MIN_SAMPLE_RATE:
            errors.append(f"Sample rate must be at least {CLONE_MIN_SAMPLE_RATE} Hz")
        if analysis["silence_ratio"] > 0.9:
            errors.append("Sample is almost entirely silence")
        analysis["errors"] = errors
        analysis["ok"] = not errors
        return analysis

    def prepare_sample(self, path: str | Path, dest_dir: Path) -> dict:
        """Validate one file and store a cleaned copy. Returns the VoiceSample fields."""
        path = require_audio_file(path)
        analysis = self.analyze_sample(path)
        if analysis["errors"]:
            raise ValidationError(f"{path.name}: {analysis['errors'][0]}", field="samples")
        y, sr = au.load(path, sr=CLONE_TARGET_SAMPLE_RATE)
        y = au.trim_silence(y, sr, threshold_db=-45.0)
        peak = au.peak_db(y)
        y = au.gain(y, -1.0 - peak) if peak > -100 else y
        stored = au.save(unique_path(dest_dir / "samples", "sample", "wav"), y, sr)
        return {
            "analysis": analysis,
            "record": {
                "path": str(stored),
                "original_name": path.name,
                "duration": round(au.duration(y, sr), 3),
                "sample_rate": sr,
                "quality": {k: analysis[k] for k in ("quality_score", "snr_db", "rms_db", "issues")},
                "sha256": sha256_file(path),
                "status": Status.ACTIVE.code,
            },
        }

    def build_profile(self, sample_paths: list[str]) -> dict:
        profiles = [extract_voice_profile(p) for p in sample_paths]
        if not profiles:
            return {}
        pitches = [p["pitch_hz"] for p in profiles if p["pitch_hz"]]
        return {
            "mfcc_mean": np.mean([p["mfcc_mean"] for p in profiles], axis=0).round(4).tolist(),
            "mfcc_std": np.mean([p["mfcc_std"] for p in profiles], axis=0).round(4).tolist(),
            "pitch_hz": round(float(np.median(pitches)), 2) if pitches else 0.0,
        }

    def select_model(self, model_key: str | None) -> dict:
        model = model_service.get(model_key or system_service.get_setting("default_clone_model"))
        if model["model_type"] not in (ModelType.CLONE, ModelType.EMBED):
            raise ModelError(f"{model['name']} cannot clone voices")
        if not model["installed"]:
            raise ModelError(f"{model['name']} is not installed. Install it on the Models page.")
        return model

    def clone(
        self,
        sample_paths: list[str | Path],
        name: str,
        consent: dict,
        *,
        language: str = "en",
        description: str = "",
        model_key: str | None = None,
        users_id: int | None = None,
        progress: Callable[[float], None] | None = None,
    ) -> dict:
        name = require_name(name)
        if not sample_paths:
            raise ValidationError("Add at least one voice sample", field="samples")
        files = [require_audio_file(p, field="samples") for p in sample_paths]
        consent_data = consent_service.validate(consent)  # no bypass: checked before any work
        model = self.select_model(model_key)
        report = progress or (lambda _v: None)

        # Heavy work (and progress reporting, which writes the jobs table) happens before the
        # transaction, so the transaction itself is short and write-only.
        staging = subdir("voices", "_staging") / uuid.uuid4().hex
        storage: str | None = None
        try:
            records = []
            for index, path in enumerate(files):
                records.append(self.prepare_sample(path, staging)["record"])
                report((index + 1) / (len(files) + 1) * 0.7)
            total = sum(r["duration"] for r in records)
            if total < CLONE_MIN_SECONDS:
                raise ValidationError(
                    f"Need at least {CLONE_MIN_SECONDS:.0f} seconds of speech in total (got {total:.1f}s)",
                    field="samples",
                )
            profile = self.build_profile([r["path"] for r in records])
            report(0.9)

            with transaction() as session:
                voice = voice_service.create_in(
                    session, name, source=CLONE, language=language, description=description,
                    model_key=model["key"], users_id=users_id, consent_status=ConsentStatus.GRANTED.code,
                )
                storage = voice.storage_dir
                consent_service.record(session, voice.voices_id, {**consent_data, "confirmed": True})
                for record in records:
                    stored = Path(storage) / "samples" / Path(record["path"]).name
                    stored.parent.mkdir(parents=True, exist_ok=True)
                    Path(record["path"]).replace(stored)
                    voice.samples.append(VoiceSample(**{**record, "path": str(stored)}))
                voice.sample_count = len(records)
                voice.profile = profile
                session.flush()
                result = voice_service.to_dict(voice, with_samples=True)
        except Exception:
            remove_tree(storage)
            raise
        finally:
            remove_tree(staging)
        logger.info(f"Cloned voice {result['voices_id']} from {len(files)} sample(s) with {model['key']}")
        report(1.0)
        return result

    def clone_async(self, sample_paths: list[str | Path], name: str, consent: dict,
                    delete_samples_after: bool = False, **kwargs) -> dict:
        """Clone in the background. `delete_samples_after` removes temporary upload files."""
        consent_service.validate(consent)  # report missing consent immediately

        def run(ctx):
            try:
                return {"voice": self.clone(sample_paths, name, consent, progress=ctx.progress, **kwargs)}
            finally:
                if delete_samples_after:
                    for path in sample_paths:
                        remove_file(path)

        return job_service.submit(JobType.VOICE_CLONE, run, title=f"Clone voice: {name}",
                                  params={"name": name, "samples": len(sample_paths)})

    def preview(self, voices_id: int, text: str = PREVIEW_TEXT, model_key: str | None = None, progress=None) -> dict:
        from app.services.tts_service import tts_service

        voice = voice_service.validate(voices_id)
        if voice["status"] != Status.ACTIVE.code:
            raise VoiceError("Only active voices can be previewed")
        audio = tts_service.preview(text, voices_id=voices_id, model_key=model_key, progress=progress)
        voice_service.update(voices_id, preview_audios_id=audio["audios_id"])
        return audio

    def preview_async(self, voices_id: int, text: str = PREVIEW_TEXT, model_key: str | None = None) -> dict:
        return job_service.submit(
            JobType.TTS,
            lambda ctx: {"audio": self.preview(voices_id, text, model_key, progress=ctx.progress)},
            title=f"Preview voice {voices_id}", params={"voices_id": voices_id},
        )


clone_service = CloneService()
