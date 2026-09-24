"""AudioService: every audio workflow — import, analysis, enhancement, editing, export.

Processing is non-destructive: each operation writes a new file and a new
`audios` row pointing at its parent; source files are never overwritten.
Internally audio is mono float32 and stored as WAV.
"""

from pathlib import Path

import numpy as np
from scipy import ndimage, signal
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.audio import (
    AI_GENERATED_TAG,
    CLIPPING_LEVEL,
    ENHANCE_PRESETS,
    EXPORT_FORMATS,
    PROCESS_STEPS,
    SILENCE_THRESHOLD_DB,
)
from app.constants.audio_source import AudioSource
from app.constants.jobs import JobType
from app.constants.status import Status
from app.exceptions import AudioError, NotFoundError, ValidationError, service_error
from app.models import Audio
from app.models.request import AudioExportRequest, AudioImportRequest, AudioProcessRequest
from app.utils import audio as au
from app.utils.database import read_session, serialize, transaction
from app.utils.files import copy_file, extension, remove_file, save_upload, subdir, unique_path
from app.utils.logger import logger
from app.utils.validation import Validation


class AudioService:
    # ------------------------------------------------------------ records

    def register(
        self,
        session: Session,
        path: str | Path,
        source: str,
        *,
        name: str = "",
        ai_generated: bool = False,
        original_path: str | Path | None = None,
        params: dict | None = None,
        projects_id: int | None = None,
        parent_audios_id: int | None = None,
        y: np.ndarray | None = None,
        sr: int | None = None,
    ) -> Audio:
        """Create an `audios` row for a file on disk inside the caller's transaction."""
        meta = au.info(path)
        loudness = None
        try:
            if y is None:
                y, sr = au.load(path)
            loudness = round(au.loudness_lufs(y, sr), 2)
        except AudioError:
            pass
        audio = Audio(
            name=name or Path(path).stem,
            path=str(path),
            original_path=str(original_path) if original_path else None,
            source=source,
            ai_generated=ai_generated,
            duration=round(meta["duration"], 3),
            sample_rate=meta["sample_rate"],
            channels=meta["channels"],
            format=meta["format"],
            codec=meta.get("codec"),
            file_size=meta.get("file_size", 0),
            loudness=loudness,
            params=params or {},
            projects_id=projects_id,
            parent_audios_id=parent_audios_id,
        )
        session.add(audio)
        session.flush()
        return audio

    def to_dict(self, audio: Audio) -> dict:
        data = serialize(audio)
        data["label"] = AI_GENERATED_TAG if audio.ai_generated else None
        return data

    def get(self, audios_id: int) -> dict:
        try:
            with read_session() as session:
                return self.to_dict(self._get(session, audios_id))
        except Exception as exc:
            raise service_error(exc, "audio_service.get")

    def _get(self, session: Session, audios_id: int) -> Audio:
        audio = session.get(Audio, audios_id)
        if audio is None or audio.status == Status.DELETED.code:
            raise NotFoundError(f"Audio {audios_id} not found", field="audios_id")
        return audio

    def list_audios(self, projects_id: int | None = None, limit: int = 100) -> list[dict]:
        try:
            with read_session() as session:
                query = select(Audio).where(Audio.status != Status.DELETED.code)
                if projects_id is not None:
                    query = query.where(Audio.projects_id == projects_id)
                rows = session.scalars(query.order_by(Audio.created_at.desc()).limit(limit))
                return [self.to_dict(a) for a in rows]
        except Exception as exc:
            raise service_error(exc, "audio_service.list_audios")

    def rename(self, audios_id: int, name: str) -> dict:
        try:
            with transaction() as session:
                audio = self._get(session, audios_id)
                audio.name = name.strip() or audio.name
                return self.to_dict(audio)
        except Exception as exc:
            raise service_error(exc, "audio_service.rename")

    def delete(self, audios_id: int) -> None:
        try:
            with transaction() as session:
                audio = self._get(session, audios_id)
                paths = {audio.path, audio.original_path}
                session.delete(audio)
            for path in paths:
                remove_file(path)
            logger.info(f"Deleted audio {audios_id}")
        except Exception as exc:
            raise service_error(exc, "audio_service.delete")

    # ------------------------------------------------------------ analysis

    def analyze(self, path: str | Path) -> dict:
        """Metadata plus quality checks used by the clone and import flows."""
        try:
            path = Validation.require_audio_file(path)
            y, sr = au.load(path)
            meta = au.info(path)
            peak = au.peak_db(y)
            rms = au.rms_db(y)
            silence = au.silence_ratio(y, sr, SILENCE_THRESHOLD_DB)
            clipping = au.clipping_ratio(y, CLIPPING_LEVEL)
            levels = au.frame_rms_db(y, sr)
            noise_floor = float(np.percentile(levels, 10)) if levels.size else -120.0
            snr = float(np.percentile(levels, 90)) - noise_floor if levels.size else 0.0

            issues = []
            if clipping > 0.001:
                issues.append("Clipping detected — record at a lower level")
            if rms < -35:
                issues.append("Very quiet recording")
            if silence > 0.5:
                issues.append("More than half of the sample is silence")
            if snr < 15:
                issues.append("High background noise")
            if meta["sample_rate"] < 16000:
                issues.append("Low sample rate (under 16 kHz)")
            score = max(0, 100 - 25 * len(issues))
            return {
                **meta,
                "duration": round(meta["duration"], 3),
                "peak_db": round(peak, 2),
                "rms_db": round(rms, 2),
                "loudness_lufs": round(au.loudness_lufs(y, sr), 2),
                "silence_ratio": round(silence, 3),
                "clipping_ratio": round(clipping, 5),
                "noise_floor_db": round(noise_floor, 2),
                "snr_db": round(snr, 2),
                "quality_score": score,
                "issues": issues,
            }
        except Exception as exc:
            raise service_error(exc, "audio_service.analyze")

    def waveform(self, audios_id: int, buckets: int = 2000) -> dict:
        try:
            audio = self.get(audios_id)
            y, sr = au.load(audio["path"])
            return {"peaks": au.waveform_peaks(y, buckets).tolist(), "duration": au.duration(y, sr), "sample_rate": sr}
        except Exception as exc:
            raise service_error(exc, "audio_service.waveform")

    # ------------------------------------------------------------ import / export

    def import_file(self, path: str | Path, projects_id: int | None = None, name: str | None = None) -> dict:
        """Copy an external file into the library (original kept) and add a WAV working copy."""
        try:
            src = Validation.require_audio_file(path)
            y, sr = au.load(src)
            original = copy_file(src, unique_path(subdir("audio", "originals"), src.stem, extension(src)))
            working = au.save(unique_path(subdir("audio"), src.stem, "wav"), y, sr)
            with transaction() as session:
                audio = self.register(
                    session, working, AudioSource.IMPORTED, name=name or src.stem, original_path=original,
                    projects_id=projects_id, y=y, sr=sr,
                )
                logger.info(f"Imported audio {audio.audios_id} ({audio.duration:.1f}s)")
                return self.to_dict(audio)
        except Exception as exc:
            raise service_error(exc, "audio_service.import_file")

    def import_upload(self, body: AudioImportRequest) -> dict:
        """import_file for an uploaded file (REST API); the temporary upload is always removed."""
        path = None
        try:
            path = save_upload(body.file)
            return self.import_file(path, body.projects_id, Path(body.file.filename or "audio").stem)
        except Exception as exc:
            raise service_error(exc, "audio_service.import_upload")
        finally:
            remove_file(path)

    def export(self, body: AudioExportRequest, dest: str | Path | None = None) -> str:
        """Write the audio in `body.format` to `dest` (default: a new file under data/exports)."""
        try:
            audio = self.get(body.audios_id)
            fmt = Validation.require_choice((body.format or "wav").lower(), EXPORT_FORMATS, "format")
            dest = Path(dest) if dest else unique_path(subdir("exports"), audio["name"], fmt)
            if extension(dest) != fmt:
                dest = dest.with_suffix(f".{fmt}")
            y, sr = au.load(audio["path"], sr=body.sample_rate)
            au.save(dest, y, sr, fmt, ai_generated=audio["ai_generated"])
            logger.info(f"Exported audio {body.audios_id} as {fmt}")
            return str(dest)
        except Exception as exc:
            raise service_error(exc, "audio_service.export")

    # ------------------------------------------------------------ enhancement pipeline

    def resolve_steps(self, steps: dict | None = None, preset: str | None = None) -> dict:
        """Merge a preset with explicit step settings; `{"step": None}` disables a step."""
        try:
            resolved: dict = {}
            if preset:
                if preset not in ENHANCE_PRESETS:
                    raise ValidationError(f"Unknown preset '{preset}'", field="preset")
                resolved.update({k: dict(v) for k, v in ENHANCE_PRESETS[preset].items()})
            for step, options in (steps or {}).items():
                if step not in PROCESS_STEPS:
                    raise ValidationError(f"Unknown processing step '{step}'", field="steps")
                if options is None or options is False:
                    resolved.pop(step, None)
                else:
                    resolved[step] = dict(options) if isinstance(options, dict) else {}
            return resolved
        except Exception as exc:
            raise service_error(exc, "audio_service.resolve_steps")

    def process_array(self, y: np.ndarray, sr: int, steps: dict) -> np.ndarray:
        """Run enabled steps in canonical order. Pure function of its inputs."""
        try:
            for step in PROCESS_STEPS:
                if step in steps:
                    y = getattr(self, f"_{step}")(y, sr, **(steps[step] or {}))
            return np.clip(y, -1.0, 1.0).astype(np.float32)
        except Exception as exc:
            raise service_error(exc, "audio_service.process_array")

    def process(self, body: AudioProcessRequest) -> dict:
        """Enhance with `steps`/`preset`, or render the edit list in `ops`, into a new audio.

        The source stays untouched.
        """
        try:
            if body.ops is not None:
                return self.render_edits(body.audios_id, body.ops)
            audios_id, preset = body.audios_id, body.preset
            resolved = self.resolve_steps(body.steps, preset)
            source = self.get(audios_id)
            y, sr = au.load(source["path"])
            out = self.process_array(y, sr, resolved)
            path = au.save(unique_path(subdir("audio"), f"{source['name']}_processed", "wav"), out, sr,
                           ai_generated=source["ai_generated"])
            with transaction() as session:
                audio = self.register(
                    session, path, AudioSource.PROCESSED, name=f"{source['name']} (processed)",
                    ai_generated=source["ai_generated"], original_path=source["original_path"] or source["path"],
                    params={"steps": resolved, "preset": preset}, projects_id=source["projects_id"],
                    parent_audios_id=audios_id, y=out, sr=sr,
                )
                logger.info(f"Processed audio {audios_id} -> {audio.audios_id} steps={list(resolved)}")
                return self.to_dict(audio)
        except Exception as exc:
            raise service_error(exc, "audio_service.process")

    def process_async(self, body: AudioProcessRequest) -> dict:
        from app.services.job_service import job_service

        try:
            return job_service.submit(JobType.AUDIO_PROCESS, lambda _ctx: {"audio": self.process(body)},
                                      title=f"Process audio {body.audios_id}",
                                      params={"audios_id": body.audios_id, "preset": body.preset})
        except Exception as exc:
            raise service_error(exc, "audio_service.process_async")

    # Individual steps (all mono float32 in, float32 out).

    def _trim_silence(self, y, sr, threshold_db: float = -45.0, pad_ms: float = 80.0):
        return au.trim_silence(y, sr, threshold_db, pad_ms)

    def _normalize(self, y, sr, peak_db: float = -1.0):
        current = au.peak_db(y)
        return au.gain(y, peak_db - current) if current > -100 else y

    def _denoise(self, y, sr, strength: float = 0.5):
        """Spectral gating against a noise profile taken from the quietest frames."""
        if y.size < 2048:
            return y
        _, _, spec = signal.stft(y, sr, nperseg=1024)
        mag = np.abs(spec)
        frame_energy = mag.mean(axis=0)
        noise = mag[:, frame_energy <= np.percentile(frame_energy, 15)].mean(axis=1, keepdims=True)
        mask = np.clip((mag - 1.5 * strength * noise) / (mag + 1e-10), 1.0 - strength, 1.0)
        mask = ndimage.uniform_filter(mask, size=(3, 5))
        _, out = signal.istft(spec * mask, sr, nperseg=1024)
        return out[: len(y)].astype(np.float32)

    def _eq(self, y, sr, highpass_hz: float = 80.0, presence_db: float = 0.0, low_db: float = 0.0,
            high_db: float = 0.0):
        if highpass_hz:
            y = au.apply_biquad(y, au.biquad("highpass", highpass_hz, sr))
        if presence_db:
            y = au.apply_biquad(y, au.biquad("peaking", 3000, sr, q=1.0, gain_db=presence_db))
        if low_db:
            y = au.apply_biquad(y, au.biquad("peaking", 200, sr, q=0.8, gain_db=low_db))
        if high_db:
            y = au.apply_biquad(y, au.biquad("highshelf", 8000, sr, gain_db=high_db))
        return y

    def _envelope_db(self, y, sr, time_ms: float):
        coeff = np.exp(-1.0 / (sr * time_ms / 1000))
        power = np.asarray(signal.lfilter([1 - coeff], [1, -coeff], y.astype(np.float64) ** 2))
        return 10 * np.log10(np.maximum(power, 1e-12))

    def _compress(self, y, sr, threshold_db: float = -20.0, ratio: float = 3.0, makeup_db: float = 0.0):
        level = self._envelope_db(y, sr, 15)
        reduction = np.maximum(level - threshold_db, 0) * (1 - 1 / max(ratio, 1.0))
        return (y * 10 ** ((makeup_db - reduction) / 20)).astype(np.float32)

    def _deess(self, y, sr, frequency: float = 6000.0, threshold_db: float = -30.0, ratio: float = 4.0):
        if sr < frequency * 2.2:
            return y
        band = au.apply_biquad(y, au.biquad("highpass", frequency, sr))
        level = self._envelope_db(band, sr, 5)
        reduction = np.maximum(level - threshold_db, 0) * (1 - 1 / ratio)
        return (y - band + band * 10 ** (-reduction / 20)).astype(np.float32)

    def _limit(self, y, sr, ceiling_db: float = -1.0):
        ceiling = 10 ** (ceiling_db / 20)
        window = max(1, int(sr * 0.005))
        peak = ndimage.maximum_filter1d(np.abs(y), size=window)
        gain = np.minimum(1.0, ceiling / np.maximum(peak, 1e-10))
        gain = ndimage.minimum_filter1d(gain, size=window)
        gain = ndimage.uniform_filter1d(gain, size=window)
        return np.clip(y * gain, -ceiling, ceiling).astype(np.float32)

    def _loudness(self, y, sr, target_lufs: float = -16.0, ceiling_db: float = -1.0):
        current = au.loudness_lufs(y, sr)
        if current <= -69:
            return y
        return self._limit(au.gain(y, target_lufs - current), sr, ceiling_db)

    # ------------------------------------------------------------ editing (non-destructive)

    def apply_edit_ops(self, y: np.ndarray, sr: int, ops: list[dict]) -> np.ndarray:
        """Replay an edit list on source audio. Times are seconds; clips are cached WAV paths."""
        try:
            for op in ops:
                kind = op.get("op")
                a = int(round(float(op.get("start", 0)) * sr))
                b = int(round(float(op.get("end", 0)) * sr))
                a, b = max(0, min(a, len(y))), max(0, min(b, len(y)))
                if kind in ("delete", "cut"):
                    y = np.concatenate([y[:a], y[b:]])
                elif kind in ("crop", "trim"):
                    y = y[a:b]
                elif kind in ("insert", "paste"):
                    clip, _ = au.load(op["clip"], sr=sr)
                    at = max(0, min(int(round(float(op["at"]) * sr)), len(y)))
                    y = np.concatenate([y[:at], clip, y[at:]])
                elif kind == "append":
                    clip, _ = au.load(op["clip"], sr=sr)
                    gap = au.silence(float(op.get("gap", 0.0)), sr)
                    y = np.concatenate([y, gap, clip])
                elif kind == "silence":
                    at = max(0, min(int(round(float(op["at"]) * sr)), len(y)))
                    y = np.concatenate([y[:at], au.silence(float(op["duration"]), sr), y[at:]])
                elif kind == "duplicate":
                    y = np.concatenate([y[:b], y[a:b], y[b:]])
                elif kind == "move":
                    segment = y[a:b]
                    rest = np.concatenate([y[:a], y[b:]])
                    to = max(0, min(int(round(float(op["to"]) * sr)), len(rest)))
                    y = np.concatenate([rest[:to], segment, rest[to:]])
                elif kind in ("gain", "volume"):
                    y = np.concatenate([y[:a], au.gain(y[a:b], float(op["db"])), y[b:]])
                elif kind == "fade_in":
                    y = np.concatenate([y[:a], au.fade(y[a:b], sr, fade_in_s=(b - a) / sr), y[b:]])
                elif kind == "fade_out":
                    y = np.concatenate([y[:a], au.fade(y[a:b], sr, fade_out_s=(b - a) / sr), y[b:]])
                elif kind == "normalize":
                    y = np.concatenate([y[:a], self._normalize(y[a:b], sr, float(op.get("peak_db", -1.0))), y[b:]])
                elif kind == "enhance":
                    steps = self.resolve_steps(op.get("steps"), op.get("preset"))
                    if b <= a:
                        y = self.process_array(y, sr, steps)
                    else:
                        y = np.concatenate([y[:a], self.process_array(y[a:b], sr, steps), y[b:]])
                else:
                    raise ValidationError(f"Unknown edit operation '{kind}'", field="ops")
            return y.astype(np.float32)
        except Exception as exc:
            raise service_error(exc, "audio_service.apply_edit_ops")

    def save_clip(self, y: np.ndarray, sr: int) -> str:
        """Persist a clipboard selection so paste/insert ops can reference it."""
        try:
            return str(au.save(unique_path(subdir("cache", "clips"), "clip", "wav"), y, sr))
        except Exception as exc:
            raise service_error(exc, "audio_service.save_clip")

    def render_edits(self, audios_id: int, ops: list[dict], name: str | None = None) -> dict:
        try:
            source = self.get(audios_id)
            y, sr = au.load(source["path"])
            out = self.apply_edit_ops(y, sr, ops)
            if out.size == 0:
                raise AudioError("The edit removes all audio")
            path = au.save(unique_path(subdir("audio"), f"{source['name']}_edit", "wav"), out, sr,
                           ai_generated=source["ai_generated"])
            with transaction() as session:
                audio = self.register(
                    session, path, AudioSource.RENDERED, name=name or f"{source['name']} (edited)",
                    ai_generated=source["ai_generated"], original_path=source["original_path"] or source["path"],
                    params={"ops": ops}, projects_id=source["projects_id"], parent_audios_id=audios_id, y=out, sr=sr,
                )
                return self.to_dict(audio)
        except Exception as exc:
            raise service_error(exc, "audio_service.render_edits")

    def materialize(self, audios_id: int, ops: list[dict] | None) -> dict:
        """The audio as edited: a new rendered audio when there are edits, else the source itself."""
        try:
            return self.render_edits(audios_id, ops) if ops else self.get(audios_id)
        except Exception as exc:
            raise service_error(exc, "audio_service.materialize")

    def join(self, audios_ids: list[int], gap_ms: int = 0, name: str = "Joined audio",
             projects_id: int | None = None) -> dict:
        try:
            if len(audios_ids) < 2:
                raise ValidationError("Select at least two audio files to join", field="audios_ids")
            sources = [self.get(i) for i in audios_ids]
            sr = max(s["sample_rate"] for s in sources)
            parts = []
            for index, source in enumerate(sources):
                y, _ = au.load(source["path"], sr=sr)
                if index:
                    parts.append(au.silence(gap_ms / 1000, sr))
                parts.append(y)
            out = au.concat(parts)
            ai = any(s["ai_generated"] for s in sources)
            path = au.save(unique_path(subdir("audio"), name, "wav"), out, sr, ai_generated=ai)
            with transaction() as session:
                audio = self.register(session, path, AudioSource.RENDERED, name=name, ai_generated=ai,
                                      params={"joined": audios_ids, "gap_ms": gap_ms}, projects_id=projects_id,
                                      y=out, sr=sr)
                return self.to_dict(audio)
        except Exception as exc:
            raise service_error(exc, "audio_service.join")

    def split(self, audios_id: int, at_seconds: float) -> list[dict]:
        try:
            source = self.get(audios_id)
            y, sr = au.load(source["path"])
            at = int(at_seconds * sr)
            if not 0 < at < len(y):
                raise ValidationError("Split point must be inside the audio", field="at")
            results = []
            with transaction() as session:
                for part, suffix in ((y[:at], "A"), (y[at:], "B")):
                    path = au.save(unique_path(subdir("audio"), f"{source['name']}_{suffix}", "wav"), part, sr,
                                   ai_generated=source["ai_generated"])
                    audio = self.register(session, path, AudioSource.RENDERED, name=f"{source['name']} ({suffix})",
                                          ai_generated=source["ai_generated"], parent_audios_id=audios_id,
                                          projects_id=source["projects_id"], y=part, sr=sr)
                    results.append(self.to_dict(audio))
            return results
        except Exception as exc:
            raise service_error(exc, "audio_service.split")

    def convert(self, audios_id: int, sample_rate: int) -> dict:
        """Resample into a new WAV (format conversion on the way out is `export`)."""
        try:
            source = self.get(audios_id)
            y, sr = au.load(source["path"], sr=sample_rate)
            path = au.save(unique_path(subdir("audio"), f"{source['name']}_{sample_rate}", "wav"), y, sr,
                           ai_generated=source["ai_generated"])
            with transaction() as session:
                audio = self.register(session, path, AudioSource.PROCESSED, name=f"{source['name']} ({sample_rate} Hz)",
                                      ai_generated=source["ai_generated"], parent_audios_id=audios_id,
                                      projects_id=source["projects_id"], y=y, sr=sr)
                return self.to_dict(audio)
        except Exception as exc:
            raise service_error(exc, "audio_service.convert")


audio_service = AudioService()
