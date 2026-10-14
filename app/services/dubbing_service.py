"""DubbingService: synchronized video dubbing, subtitle alignment, and video remuxing.

Integrates FFmpeg media probing, SRT/WebVTT transcription alignment, multi-speaker voice mapping,
line-by-line synthesis with timing conflict detection, and non-destructive audio ducking & video remuxing.
"""

from collections.abc import Callable
from pathlib import Path

import numpy as np
import soundfile as sf
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.audio_source import AudioSource
from app.constants.status import Status
from app.exceptions import NotFoundError, ValidationError, service_error
from app.models.audio import Audio
from app.models.dubbing import DubbingProject, DubbingSegment
from app.models.request.dubbing_import_request import DubbingImportRequest
from app.models.request.dubbing_project_request import DubbingProjectRequest
from app.models.request.dubbing_render_request import DubbingRenderRequest
from app.models.request.dubbing_segment_request import DubbingSegmentRequest
from app.models.request.tts_request import TTSRequest
from app.services.audio_service import audio_service
from app.services.system_service import system_service
from app.services.tts_service import tts_service
from app.services.voice_service import voice_service
from app.utils import audio as au
from app.utils import ffmpeg
from app.utils.database import deleted_result, read_session, serialize, transaction
from app.utils.files import data_dir, subdir, unique_path
from app.utils.logger import logger
from app.utils.subtitles import parse_subtitles, to_srt, to_vtt
from app.utils.validation import Validation


def compute_segment_metrics(segment: DubbingSegment | dict) -> dict:
    """Calculate slot duration and timing conflict metrics without silent audio warping."""
    start_ms = segment.start_ms if isinstance(segment, DubbingSegment) else segment.get("start_ms", 0)
    end_ms = segment.end_ms if isinstance(segment, DubbingSegment) else segment.get("end_ms", 0)
    gen_ms = segment.generated_duration_ms if isinstance(segment, DubbingSegment) else segment.get("generated_duration_ms")

    slot_ms = max(0, int(end_ms) - int(start_ms))
    if gen_ms is None:
        return {
            "slot_duration_ms": slot_ms,
            "delta_ms": None,
            "conflict_type": "none",
            "conflict_message": "Not generated yet",
        }

    delta_ms = int(gen_ms) - slot_ms
    if delta_ms > 100:
        conflict_type = "overflow"
        conflict_message = f"Audio is {delta_ms} ms too long for slot (+{round(delta_ms/1000, 2)} s)"
    elif delta_ms < -300:
        conflict_type = "underflow"
        conflict_message = f"Audio is {abs(delta_ms)} ms shorter than slot (-{round(abs(delta_ms)/1000, 2)} s)"
    else:
        conflict_type = "ok"
        conflict_message = "Synchronized (within tolerance)"

    return {
        "slot_duration_ms": slot_ms,
        "delta_ms": delta_ms,
        "conflict_type": conflict_type,
        "conflict_message": conflict_message,
    }


def duck_and_mix(bg: np.ndarray, fg: np.ndarray, sr: int, duck_volume: float = 0.25) -> np.ndarray:
    """Mix foreground dialogue onto background audio with smooth ducking envelope."""
    max_len = max(len(bg), len(fg))
    if len(bg) < max_len:
        bg = np.pad(bg, (0, max_len - len(bg)))
    if len(fg) < max_len:
        fg = np.pad(fg, (0, max_len - len(fg)))

    # Compute smoothed envelope of dialogue activity
    abs_fg = np.abs(fg)
    win_size = max(1, int(0.04 * sr))  # 40 ms window
    kernel = np.ones(win_size, dtype=np.float32) / win_size
    smoothed = np.convolve(abs_fg, kernel, mode="same")

    # Generate smooth ducking attenuation curve
    threshold = 0.01
    active = smoothed > threshold
    raw_envelope = np.where(active, float(duck_volume), 1.0).astype(np.float32)

    # Smooth attack and release to eliminate clicks
    smooth_win = max(1, int(0.08 * sr))  # 80 ms smoothing
    smooth_kernel = np.ones(smooth_win, dtype=np.float32) / smooth_win
    envelope = np.convolve(raw_envelope, smooth_kernel, mode="same")
    envelope = np.clip(envelope, float(duck_volume), 1.0)

    mixed = bg * envelope + fg
    peak = float(np.abs(mixed).max()) if mixed.size else 0.0
    if peak > 0.98:
        mixed = mixed * (0.95 / peak)
    return mixed.astype(np.float32)


class DubbingService:
    # ------------------------------------------------------------ serialization

    def segment_dict(self, segment: DubbingSegment) -> dict:
        data = serialize(segment)
        data.update(compute_segment_metrics(segment))
        return data

    def to_dict(self, project: DubbingProject, with_segments: bool = True) -> dict:
        data = serialize(project)
        if with_segments:
            segments = [self.segment_dict(s) for s in project.segments]
            data["segments"] = segments
            speakers = []
            for s in project.segments:
                if s.speaker and s.speaker not in speakers:
                    speakers.append(s.speaker)
            data["speakers"] = speakers
            data["total_segments"] = len(segments)
            data["generated_segments"] = sum(1 for s in segments if s.get("audios_id"))
            data["conflict_segments"] = sum(1 for s in segments if s.get("conflict_type") == "overflow")
        return data

    def _get(self, session: Session, dubbing_projects_id: int) -> DubbingProject:
        project = session.get(DubbingProject, dubbing_projects_id)
        if project is None or project.status == Status.DELETED.code:
            raise NotFoundError(f"Dubbing project {dubbing_projects_id} not found", field="dubbing_projects_id")
        return project

    def _segment(self, session: Session, dubbing_segments_id: int) -> DubbingSegment:
        segment = session.get(DubbingSegment, dubbing_segments_id)
        if segment is None or segment.status == Status.DELETED.code:
            raise NotFoundError(f"Dubbing segment {dubbing_segments_id} not found", field="dubbing_segments_id")
        return segment

    # ------------------------------------------------------------ CRUD

    def create(self, title: str | None, source_media_path: str, source_language: str = "en",
               target_language: str = "en", speaker_map: dict | None = None,
               settings: dict | None = None) -> dict:
        try:
            media = Path(source_media_path)
            if not media.is_file():
                raise ValidationError(f"Media file not found: {source_media_path}", field="source_media_path")

            probe = ffmpeg.probe_media(media) if ffmpeg.available() else {}
            duration = float(probe.get("duration") or 0.0)

            with transaction() as session:
                source_audio_id = None
                if probe.get("has_audio") and ffmpeg.available():
                    # Extract original audio for reference & background ducking
                    audio_dir = subdir("audio")
                    dst_wav = unique_path(audio_dir / f"dub_source_{media.stem}.wav")
                    ffmpeg.extract_audio(media, dst_wav)
                    audio_row = audio_service.register(
                        session,
                        name=f"{media.stem} (Source Audio)",
                        path=dst_wav,
                        duration=duration,
                        sample_rate=int(probe.get("sample_rate") or 44100),
                        channels=int(probe.get("channels") or 1),
                        source=AudioSource.IMPORT.value,
                    )
                    source_audio_id = audio_row.audios_id

                project = DubbingProject(
                    title=Validation.require_name(title or media.stem, "title", 200),
                    source_media_path=str(media.resolve()),
                    source_audio_id=source_audio_id,
                    source_language=source_language or "en",
                    target_language=target_language or "en",
                    speaker_map=speaker_map or {},
                    settings=settings or {},
                    duration_seconds=duration,
                    video_width=probe.get("width"),
                    video_height=probe.get("height"),
                    video_fps=probe.get("fps"),
                )
                session.add(project)
                session.flush()
                logger.info(f"Created dubbing project {project.dubbing_projects_id}: '{project.title}'")
                return self.to_dict(project)
        except Exception as exc:
            raise service_error(exc, "dubbing_service.create")

    def get(self, dubbing_projects_id: int) -> dict:
        try:
            with read_session() as session:
                return self.to_dict(self._get(session, dubbing_projects_id))
        except Exception as exc:
            raise service_error(exc, "dubbing_service.get")

    def list_projects(self) -> list[dict]:
        try:
            with read_session() as session:
                query = select(DubbingProject).where(DubbingProject.status != Status.DELETED.code)
                projects = session.scalars(query.order_by(DubbingProject.updated_at.desc())).all()
                return [self.to_dict(p, with_segments=False) for p in projects]
        except Exception as exc:
            raise service_error(exc, "dubbing_service.list_projects")

    def update(self, dubbing_projects_id: int, title: str | None = None,
               source_language: str | None = None, target_language: str | None = None,
               speaker_map: dict | None = None, settings: dict | None = None) -> dict:
        try:
            with transaction() as session:
                project = self._get(session, dubbing_projects_id)
                if title is not None:
                    project.title = Validation.require_name(title, "title", 200)
                if source_language is not None:
                    project.source_language = source_language
                if target_language is not None:
                    project.target_language = target_language
                if speaker_map is not None:
                    project.speaker_map = {k: v for k, v in speaker_map.items() if v}
                if settings is not None:
                    project.settings = {**(project.settings or {}), **settings}
                return self.to_dict(project)
        except Exception as exc:
            raise service_error(exc, "dubbing_service.update")

    def delete(self, dubbing_projects_id: int) -> None:
        try:
            with transaction() as session:
                project = self._get(session, dubbing_projects_id)
                project.status = Status.DELETED.code
                for seg in project.segments:
                    seg.status = Status.DELETED.code
                logger.info(f"Deleted dubbing project {dubbing_projects_id}")
        except Exception as exc:
            raise service_error(exc, "dubbing_service.delete")

    def save(self, body: DubbingProjectRequest) -> dict:
        """One entry point: create (no id), delete (status = Deleted) or update."""
        try:
            if body.dubbing_projects_id is None:
                if not body.source_media_path:
                    raise ValidationError("source_media_path is required to create a dubbing project", field="source_media_path")
                return self.create(
                    title=body.title,
                    source_media_path=body.source_media_path,
                    source_language=body.source_language or "en",
                    target_language=body.target_language or "en",
                    speaker_map=body.speaker_map,
                    settings=body.settings,
                )
            if body.status == Status.DELETED.code:
                self.delete(body.dubbing_projects_id)
                return deleted_result("dubbing_projects_id", body.dubbing_projects_id)
            return self.update(
                dubbing_projects_id=body.dubbing_projects_id,
                title=body.title,
                source_language=body.source_language,
                target_language=body.target_language,
                speaker_map=body.speaker_map,
                settings=body.settings,
            )
        except Exception as exc:
            raise service_error(exc, "dubbing_service.save")

    # ------------------------------------------------------------ Subtitle Import / Export

    def import_subtitles(self, dubbing_projects_id: int, content: str,
                         format: str = "srt", replace_existing: bool = True) -> dict:
        try:
            parsed = parse_subtitles(content, format=format)
            if not parsed:
                raise ValidationError("No valid subtitle segments could be parsed", field="content")

            with transaction() as session:
                project = self._get(session, dubbing_projects_id)
                start_pos = 0 if replace_existing else len(project.segments)
                new_segments = [
                    DubbingSegment(
                        dubbing_projects_id=dubbing_projects_id,
                        position=start_pos + i,
                        start_ms=item["start_ms"],
                        end_ms=item["end_ms"],
                        speaker=item["speaker"],
                        source_text=item["text"],
                        target_text=item["text"],
                    )
                    for i, item in enumerate(parsed)
                ]
                if replace_existing:
                    project.segments[:] = new_segments
                else:
                    project.segments.extend(new_segments)
                session.flush()
                logger.info(f"Imported {len(parsed)} subtitle segments into project {dubbing_projects_id}")
            return self.get(dubbing_projects_id)
        except Exception as exc:
            raise service_error(exc, "dubbing_service.import_subtitles")

    def export_subtitles(self, dubbing_projects_id: int, format: str = "srt", use_target: bool = True) -> str:
        try:
            with read_session() as session:
                project = self._get(session, dubbing_projects_id)
                text_key = "target_text" if use_target else "source_text"
                raw = [
                    {"start_ms": s.start_ms, "end_ms": s.end_ms, "speaker": s.speaker, text_key: getattr(s, text_key)}
                    for s in project.segments
                ]
                fmt = format.lower().strip().lstrip(".")
                return to_vtt(raw, text_key=text_key) if fmt == "vtt" else to_srt(raw, text_key=text_key)
        except Exception as exc:
            raise service_error(exc, "dubbing_service.export_subtitles")

    # ------------------------------------------------------------ Segments CRUD

    def save_segment(self, body: DubbingSegmentRequest) -> dict:
        try:
            with transaction() as session:
                if body.dubbing_segments_id is None:
                    if body.dubbing_projects_id is None:
                        raise ValidationError("dubbing_projects_id is required", field="dubbing_projects_id")
                    project = self._get(session, body.dubbing_projects_id)
                    pos = body.position if body.position is not None else len(project.segments)
                    seg = DubbingSegment(
                        dubbing_projects_id=body.dubbing_projects_id,
                        position=pos,
                        start_ms=body.start_ms or 0,
                        end_ms=body.end_ms or 0,
                        speaker=body.speaker or "Narrator",
                        source_text=body.source_text or "",
                        target_text=body.target_text or body.source_text or "",
                        voices_id=body.voices_id,
                        speed=body.speed,
                        pitch=body.pitch,
                        emotion=body.emotion,
                        locked=bool(body.locked),
                    )
                    session.add(seg)
                    session.flush()
                    return self.segment_dict(seg)

                seg = self._segment(session, body.dubbing_segments_id)
                if body.status == Status.DELETED.code:
                    session.delete(seg)
                    return deleted_result("dubbing_segments_id", body.dubbing_segments_id)

                for field in ("start_ms", "end_ms", "speaker", "source_text", "target_text",
                              "voices_id", "speed", "pitch", "emotion", "locked", "position"):
                    val = getattr(body, field, None)
                    if val is not None:
                        setattr(seg, field, val)
                session.flush()
                return self.segment_dict(seg)
        except Exception as exc:
            raise service_error(exc, "dubbing_service.save_segment")

    # ------------------------------------------------------------ Speaker Mapping

    def auto_map_speakers(self, dubbing_projects_id: int) -> dict:
        """Detect speakers in segments and map them to available voices."""
        try:
            with transaction() as session:
                project = self._get(session, dubbing_projects_id)
                speakers = []
                for s in project.segments:
                    if s.speaker and s.speaker not in speakers:
                        speakers.append(s.speaker)

                voices = voice_service.list_voices()
                available_ids = [v["voices_id"] for v in voices]
                if not available_ids:
                    return self.to_dict(project)

                current_map = dict(project.speaker_map or {})
                for idx, speaker in enumerate(speakers):
                    if speaker not in current_map or not current_map[speaker]:
                        # Assign next available voice round-robin
                        current_map[speaker] = available_ids[idx % len(available_ids)]

                project.speaker_map = current_map
                session.flush()
                logger.info(f"Auto-mapped speakers for project {dubbing_projects_id}: {current_map}")
                return self.to_dict(project)
        except Exception as exc:
            raise service_error(exc, "dubbing_service.auto_map_speakers")

    # ------------------------------------------------------------ Synthesis & Conflict Detection

    def generate_segment(self, dubbing_segments_id: int) -> dict:
        """Synthesize TTS for a single line and calculate conflict metrics."""
        try:
            with read_session() as session:
                segment = self._segment(session, dubbing_segments_id)
                project = segment.project
                text = (segment.target_text or segment.source_text or "").strip()
                if not text:
                    raise ValidationError("Segment has no text to synthesize", field="target_text")

                voice_id = segment.voices_id or (project.speaker_map or {}).get(segment.speaker)
                speed = segment.speed or 1.0
                pitch = segment.pitch or 1.0
                emotion = segment.emotion or "neutral"

            # Generate audio via TTS service
            tts_req = TTSRequest(
                text=text,
                voices_id=voice_id,
                speed=speed,
                pitch=pitch,
                emotion=emotion,
            )
            result = tts_service.generate(tts_req)
            gen_duration_ms = int(result["duration"] * 1000)

            with transaction() as session:
                segment = self._segment(session, dubbing_segments_id)
                segment.audios_id = result["audios_id"]
                segment.generated_duration_ms = gen_duration_ms
                session.flush()
                logger.info(
                    f"Generated segment {dubbing_segments_id} (duration {gen_duration_ms} ms, slot {segment.end_ms - segment.start_ms} ms)"
                )
                return self.segment_dict(segment)
        except Exception as exc:
            raise service_error(exc, "dubbing_service.generate_segment")

    def generate_all(self, dubbing_projects_id: int, overwrite_existing: bool = False,
                     cancelled: Callable[[], bool] | None = None) -> dict:
        """Generate speech for all pending or unlocked segments in project."""
        try:
            with read_session() as session:
                project = self._get(session, dubbing_projects_id)
                segment_ids = [
                    s.dubbing_segments_id for s in project.segments
                    if not s.locked and (overwrite_existing or not s.audios_id)
                ]

            for seg_id in segment_ids:
                if cancelled and cancelled():
                    logger.info("Batch dubbing generation cancelled")
                    break
                self.generate_segment(seg_id)

            return self.get(dubbing_projects_id)
        except Exception as exc:
            raise service_error(exc, "dubbing_service.generate_all")

    # ------------------------------------------------------------ Timeline Render & Video Remux

    def render_dialogue_timeline(self, dubbing_projects_id: int) -> int:
        """Join all generated segment takes onto a master timeline with silence padding."""
        try:
            with read_session() as session:
                project = self._get(session, dubbing_projects_id)
                segments = list(project.segments)
                if not segments:
                    raise ValidationError("Dubbing project has no segments to render")

                target_sr = system_service.get_setting("sample_rate") or 44100
                total_duration = max(
                    project.duration_seconds,
                    max((s.end_ms for s in segments), default=0) / 1000.0,
                )
                total_samples = max(target_sr, int(total_duration * target_sr) + target_sr)
                timeline = np.zeros(total_samples, dtype=np.float32)

                rendered_count = 0
                for s in segments:
                    if not s.audios_id:
                        continue
                    audio_row = session.get(Audio, s.audios_id)
                    if not audio_row or not Path(audio_row.file_path).is_file():
                        continue
                    y, _ = au.load(audio_row.file_path, sr=target_sr)
                    start_sample = int(s.start_ms * target_sr / 1000)
                    end_sample = min(start_sample + len(y), len(timeline))
                    copy_len = end_sample - start_sample
                    if copy_len > 0:
                        timeline[start_sample:end_sample] += y[:copy_len]
                        rendered_count += 1

                if rendered_count == 0:
                    raise ValidationError("No generated dialogue audio found to render")

                # Normalize peak if necessary
                peak = float(np.abs(timeline).max()) if timeline.size else 0.0
                if peak > 0.98:
                    timeline = timeline * (0.95 / peak)

            out_dir = subdir("audio")
            out_file = unique_path(out_dir / f"dub_dialogue_{dubbing_projects_id}.wav")
            au.save(out_file, timeline, target_sr)

            with transaction() as session:
                audio_row = audio_service.register(
                    session,
                    name=f"{project.title} (Dubbed Dialogue)",
                    path=out_file,
                    duration=float(len(timeline) / target_sr),
                    sample_rate=target_sr,
                    channels=1,
                    source=AudioSource.GENERATED.value,
                    ai_generated=True,
                )
                project = self._get(session, dubbing_projects_id)
                project.target_audio_id = audio_row.audios_id
                session.flush()
                return audio_row.audios_id
        except Exception as exc:
            raise service_error(exc, "dubbing_service.render_dialogue_timeline")

    def render_video(self, body: DubbingRenderRequest) -> dict:
        """Render final synchronized video with dubbed dialogue and optional background ducking."""
        try:
            if not ffmpeg.available():
                raise ValidationError("FFmpeg is required for video remuxing and rendering")

            with read_session() as session:
                project = self._get(session, body.dubbing_projects_id)
                source_video = Path(project.source_media_path)
                if not source_video.is_file():
                    raise NotFoundError(f"Source video file not found: {project.source_media_path}")

                target_audio_id = project.target_audio_id

            if not target_audio_id:
                target_audio_id = self.render_dialogue_timeline(body.dubbing_projects_id)

            with read_session() as session:
                project = self._get(session, body.dubbing_projects_id)
                dialogue_audio_row = session.get(Audio, target_audio_id)
                if not dialogue_audio_row or not Path(dialogue_audio_row.file_path).is_file():
                    raise NotFoundError("Rendered dialogue audio file not found")
                dialogue_path = Path(dialogue_audio_row.file_path)

                source_audio_row = session.get(Audio, project.source_audio_id) if project.source_audio_id else None
                bg_path = Path(source_audio_row.file_path) if source_audio_row and Path(source_audio_row.file_path).is_file() else None

            # Prepare final audio track
            sr = system_service.get_setting("sample_rate") or 44100
            mixed_audio_path = dialogue_path
            if bg_path and body.background_audio_mode == "duck":
                bg_y, _ = au.load(bg_path, sr=sr)
                fg_y, _ = au.load(dialogue_path, sr=sr)
                mixed = duck_and_mix(bg_y, fg_y, sr=sr, duck_volume=body.ducking_volume)
                mixed_audio_path = unique_path(subdir("audio") / f"dub_mixed_{body.dubbing_projects_id}.wav")
                au.save(mixed_audio_path, mixed, sr=sr)
            elif bg_path and body.background_audio_mode == "replace":
                mixed_audio_path = dialogue_path

            # Output video destination
            export_dir = subdir("exports")
            out_video = Path(body.output_path) if body.output_path else unique_path(export_dir / f"dubbed_{source_video.stem}.mp4")
            out_video.parent.mkdir(parents=True, exist_ok=True)

            ffmpeg.remux_video(
                video_path=source_video,
                audio_path=mixed_audio_path,
                dst_path=out_video,
                video_mode=body.video_quality,
                audio_bitrate=body.audio_bitrate,
            )

            with transaction() as session:
                project = self._get(session, body.dubbing_projects_id)
                project.output_video_path = str(out_video.resolve())
                session.flush()
                logger.info(f"Rendered dubbed video for project {body.dubbing_projects_id}: {out_video}")
                return self.to_dict(project)
        except Exception as exc:
            raise service_error(exc, "dubbing_service.render_video")


dubbing_service = DubbingService()
