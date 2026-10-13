"""TTSService: text → speech with a chosen voice and model, then clean-up.

Flow: validate → resolve voice → resolve model → synthesize (chunked) →
shape prosody → save the untouched original → post-process → audios record.

A generation is planned once (voice, model, prosody, engine limits), then its chunks
go to the engine, several per call when the engine batches. Per-sentence generation
shares the plan, so every sentence uses the same voice and settings in order. Each
result carries `timings`: model loading, inference, prosody, post-processing, file
writes and database time, plus the audio length and real-time factor.
"""

import dataclasses
import hashlib
import json
import re
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import numpy as np

from app.constants.audio import (
    DEFAULT_TTS_POST,
    EMOTIONS,
    PAUSE_SENTENCE_MS,
    STYLE_PRESETS,
    TTS_CHUNK_CHARS,
)
from app.constants.audio_source import AudioSource
from app.constants.jobs import JobType
from app.exceptions import ValidationError, service_error
from app.models.request import RegenerateRequest, TTSRequest
from app.services.audio_service import audio_service
from app.services.job_service import job_service
from app.services.model_service import model_service
from app.services.system_service import system_service
from app.services.voice_service import CLONE, voice_service
from app.utils import audio as au
from app.utils.database import transaction
from app.utils.files import subdir, unique_path
from app.utils.logger import logger
from app.utils.model import SynthesisRequest, VoiceRef, apply_prosody
from app.utils.validation import Validation

# progress(value 0..1, message=None); JobContext.progress and JobContext.sub fit.
Progress = Callable[..., None]

_SENTENCE_END = re.compile(r"(?<=[.!?…])[\"')\]]*\s+(?=[\"'(\[]?[A-Z0-9À-ÖØ-Þ])")
_PAUSE_TAG = re.compile(r"\[pause(?:\s+(\d+)\s*(ms|s)?)?\]", re.IGNORECASE)


def split_sentences(text: str) -> list[str]:
    """Split text into sentences, keeping [pause] tags attached to their sentence."""
    sentences = []
    for paragraph in re.split(r"\n\s*\n", text.strip()):
        paragraph = " ".join(paragraph.split())
        if paragraph:
            sentences.extend(s.strip() for s in _SENTENCE_END.split(paragraph) if s.strip())
    return sentences


def _chunks(text: str, max_chars: int = TTS_CHUNK_CHARS) -> list[tuple[str, int]]:
    """(text, pause_after_ms) chunks no longer than `max_chars`, honouring [pause N] tags."""
    pieces: list[tuple[str, int]] = []
    position = 0
    for match in _PAUSE_TAG.finditer(text):
        pieces.append((text[position : match.start()], 0))
        amount = int(match.group(1) or 500)
        pieces.append(("", amount * 1000 if (match.group(2) or "ms").lower() == "s" else amount))
        position = match.end()
    pieces.append((text[position:], 0))

    chunks: list[tuple[str, int]] = []
    for piece, pause in pieces:
        if not piece.strip():
            if chunks and pause:
                # -1 means "default sentence gap"; an explicit pause replaces it.
                chunks[-1] = (chunks[-1][0], max(chunks[-1][1], 0) + pause)
            continue
        current = ""
        for sentence in split_sentences(piece):
            if current and len(current) + len(sentence) + 1 > max_chars:
                chunks.append((current, -1))
                current = sentence
            else:
                current = f"{current} {sentence}".strip()
        if current:
            chunks.append((current, -1))
    return chunks


def apply_pronunciations(text: str, pronunciations: dict[str, str] | None) -> str:
    for word, spoken in (pronunciations or {}).items():
        if word.strip():
            text = re.sub(rf"\b{re.escape(word.strip())}\b", spoken, text, flags=re.IGNORECASE)
    return text


class _Clock:
    """Seconds spent per stage of one generation."""

    def __init__(self):
        self.started = time.perf_counter()
        self.stages: dict[str, float] = {}

    @contextmanager
    def __call__(self, stage: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            self.add(stage, time.perf_counter() - start)

    def add(self, stage: str, seconds: float) -> None:
        self.stages[stage] = self.stages.get(stage, 0.0) + seconds

    def report(self, audio_s: float, **extra) -> dict:
        total_s = round(time.perf_counter() - self.started, 3)
        audio_s = round(audio_s, 3)
        return {**{f"{stage}_s": round(value, 3) for stage, value in self.stages.items()},
                "total_s": total_s, "audio_s": audio_s,
                "rtf": round(total_s / audio_s, 3) if audio_s else None, **extra}


@dataclass
class _Plan:
    """What a generation resolved once: voice, model, effective prosody and engine limits."""

    text: str
    info: dict
    model: dict
    voice: dict | None
    voice_ref: VoiceRef | None
    native: frozenset[str]
    supports_cloning: bool
    request: SynthesisRequest
    speed: float
    pitch: float
    energy: float
    gap_ms: int
    chunk_chars: int
    batch: int
    pronunciations: dict[str, str]


def _report(progress: Progress | None, value: float, message: str | None = None) -> None:
    if progress:
        progress(value, message)


def _eta(done_chars: int, total_chars: int, elapsed: float) -> str:
    """Time left at the speed so far; only once a chunk has finished, so it is never a guess."""
    if not done_chars or done_chars >= total_chars:
        return ""
    left = elapsed / done_chars * (total_chars - done_chars)
    return f" · about {left:.0f} s left" if left >= 1 else " · almost done"


class TTSService:
    # ------------------------------------------------------------ planning and synthesis

    def _plan(self, body: TTSRequest, clock: _Clock, progress: Progress | None = None) -> _Plan:
        text = Validation.require_text(body.text)
        speed = Validation.in_range(body.speed, 0.5, 2.0, "speed", 1.0)
        pitch = Validation.in_range(body.pitch, 0.5, 2.0, "pitch", 1.0)
        energy = Validation.in_range(body.energy, 0.1, 2.0, "energy", 1.0)
        emotion = Validation.require_emotion(body.emotion)
        style = Validation.require_choice(body.style or "default", STYLE_PRESETS, "style")
        temperature = body.temperature
        if temperature is not None:
            temperature = Validation.in_range(temperature, 0.1, 1.5, "temperature", 0.7)
        engine_voice = Validation.optional_engine_voice(body.engine_voice)
        voices_id, seed, pause_ms = body.voices_id, body.seed, body.pause_ms

        voice_ref, voice = (None, None)
        if voices_id:
            voice_ref, voice = voice_service.voice_ref(voices_id)
        if engine_voice:
            voice_ref = dataclasses.replace(voice_ref, engine_voice=engine_voice) if voice_ref \
                else VoiceRef(engine_voice=engine_voice)
        model = model_service.resolve_speech_model(body.model_key, voice)
        if not model["loaded"]:
            _report(progress, 0.0, f"Loading {model['name']}")
        with clock("load"):
            backend = model_service.backend_for(model["key"])
        native = backend.native_params

        # Combine style and emotion presets with the explicit settings.
        style_preset = STYLE_PRESETS[style]
        emotion_preset = EMOTIONS["neutral"] if "emotion" in native else EMOTIONS[emotion]
        eff_speed = speed * style_preset["speed"] * emotion_preset["speed"]
        eff_pitch = pitch * emotion_preset["pitch"]
        eff_energy = energy * emotion_preset["energy"]
        gap_ms = max(0, (PAUSE_SENTENCE_MS if pause_ms is None else pause_ms) + style_preset["pause_ms"])

        request = SynthesisRequest(
            text="", language=(voice or {}).get("language") or "en",
            speed=eff_speed if "speed" in native else 1.0, pitch=eff_pitch if "pitch" in native else 1.0,
            emotion=emotion, style=style, temperature=temperature, seed=seed,
        )
        info = {
            "text": text,
            "voices_id": voices_id,
            "voice_name": voice["name"] if voice else None,
            "engine_voice": engine_voice,
            "model_key": model["key"],
            "online": model["online"],
            "cloned": bool(voice and voice["source"] == CLONE and backend.supports_cloning),
            "pitch_matched": False,
            "speed": speed, "pitch": pitch, "energy": energy, "emotion": emotion, "style": style,
            "pause_ms": pause_ms, "pronunciations": body.pronunciations or {},
            "temperature": temperature, "seed": seed,
        }
        batch = max(1, min(backend.max_batch, int(system_service.get_setting("batch_size") or 1)))
        chunk_chars = (backend.batch_chunk_chars if batch > 1 and backend.batch_chunk_chars
                       else backend.max_chunk_chars or TTS_CHUNK_CHARS)
        return _Plan(text=text, info=info, model=model, voice=voice, voice_ref=voice_ref, native=native,
                     supports_cloning=backend.supports_cloning, request=request, speed=eff_speed, pitch=eff_pitch,
                     energy=eff_energy, gap_ms=gap_ms, chunk_chars=chunk_chars, batch=batch,
                     pronunciations=body.pronunciations or {})

    def _speak(self, plan: _Plan, texts: list[str], clock: _Clock, progress: Progress | None = None,
               span: tuple[float, float] = (0.0, 0.8)) -> list[tuple[np.ndarray, int]]:
        """Raw speech for each text, in order: its chunks joined with the sentence gap or [pause] lengths.

        Chunks go to the engine `plan.batch` at a time (one at a time unless the engine batches). Between
        calls the model is free, so another job on the same model can take its turn.
        """
        chunked = [_chunks(apply_pronunciations(text, plan.pronunciations), plan.chunk_chars) for text in texts]
        if not all(chunked):
            raise ValidationError("There is nothing to speak in this text", field="text")
        flat = [(index, chunk, pause) for index, chunks in enumerate(chunked) for chunk, pause in chunks]
        total_chars = sum(len(chunk) for _, chunk, _ in flat)
        logger.info(f"TTS: {total_chars} characters in {len(flat)} chunk(s) with {plan.model['key']}"
                    + (f", {plan.batch} per call" if plan.batch > 1 else ""))
        spoken: list[tuple[np.ndarray, int]] = []
        done_chars, audio_s, started = 0, 0.0, time.perf_counter()
        for start in range(0, len(flat), plan.batch):
            group = flat[start : start + plan.batch]
            requests = [dataclasses.replace(plan.request, text=chunk) for _, chunk, _ in group]
            waiting = time.perf_counter()
            with model_service.using(plan.model["key"]) as backend:
                clock.add("model_wait", time.perf_counter() - waiting)  # another job's chunk on the same model
                with clock("inference"):
                    outputs = backend.synthesize_batch(requests, plan.voice_ref) if len(requests) > 1 \
                        else [backend.synthesize(requests[0], plan.voice_ref)]
            spoken.extend(outputs)
            done_chars += sum(len(request.text) for request in requests)
            audio_s += sum(au.duration(y, sr) for y, sr in outputs)
            elapsed = time.perf_counter() - started
            message = (f"Chunk {min(start + len(group), len(flat))} of {len(flat)} · {audio_s:.1f} s of audio · "
                       f"RTF {elapsed / audio_s:.2f}" if audio_s else "Generating") + _eta(done_chars, total_chars, elapsed)
            _report(progress, span[0] + (span[1] - span[0]) * done_chars / max(total_chars, 1), message)

        results: list[tuple[np.ndarray, int]] = []
        position = 0
        for chunks in chunked:
            parts: list[np.ndarray] = []
            sr = 0
            for _chunk, pause_after in chunks:
                y, chunk_sr = spoken[position]
                position += 1
                if sr and chunk_sr != sr:
                    y = au.resample(y, chunk_sr, sr)
                sr = sr or chunk_sr
                parts.append(au.to_mono(y).astype(np.float32))
                parts.append(au.silence((plan.gap_ms if pause_after < 0 else pause_after) / 1000, sr))
            results.append((au.concat(parts[:-1]), sr))
        return results

    def _shape(self, plan: _Plan, y: np.ndarray, sr: int) -> tuple[np.ndarray, bool]:
        """Prosody the engine did not apply itself, and a cloned voice's pitch on engines that cannot clone."""
        pitch_match = 1.0
        voice, voice_ref = plan.voice, plan.voice_ref
        if voice and voice_ref and voice["source"] == CLONE and not plan.supports_cloning and voice_ref.pitch_hz:
            generated = au.estimate_pitch_hz(y, sr)
            if generated:
                pitch_match = float(np.clip(voice_ref.pitch_hz / generated, 0.6, 1.6))
        y = apply_prosody(
            y, sr,
            speed=1.0 if "speed" in plan.native else plan.speed,
            pitch=(1.0 if "pitch" in plan.native else plan.pitch) * pitch_match,
            energy=plan.energy,
        )
        return y, pitch_match != 1.0

    def _synthesize(self, body: TTSRequest, clock: _Clock, progress: Progress | None) -> tuple[np.ndarray, int, dict]:
        plan = self._plan(body, clock, progress)
        ((y, sr),) = self._speak(plan, [plan.text], clock, progress)
        with clock("prosody"):
            y, matched = self._shape(plan, y, sr)
        _report(progress, 0.9, "Cleaning up")
        info = {**plan.info, "pitch_matched": matched}
        logger.info(f"TTS generated {au.duration(y, sr):.1f}s with {plan.model['key']} (voice={plan.info['voices_id']})")
        return y, sr, info

    def synthesize(self, body: TTSRequest, progress: Progress | None = None) -> tuple[np.ndarray, int, dict]:
        """Generate raw speech in memory. Returns (audio, sample_rate, generation info)."""
        try:
            clock = _Clock()
            y, sr, info = self._synthesize(body, clock, progress)
            return y, sr, {**info, "timings": clock.report(au.duration(y, sr))}
        except Exception as exc:
            raise service_error(exc, "tts_service.synthesize")

    def cache_key(self, body: TTSRequest) -> str:
        """Everything that changes the sound: text, settings, the resolved model and the voice's version."""
        try:
            voice = voice_service.get(body.voices_id, with_samples=False) if body.voices_id else None
            model = model_service.resolve_speech_model(body.model_key, voice)
            settings = body.model_dump(exclude={"name", "background", "cache"})
            blob = json.dumps({**settings, "model_key": model["key"], "voice_version": (voice or {}).get("updated_at")},
                              sort_keys=True, default=str)
            return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]
        except Exception as exc:
            raise service_error(exc, "tts_service.cache_key")

    # ------------------------------------------------------------ saving

    def _write(self, body: TTSRequest, y: np.ndarray, sr: int, info: dict, clock: _Clock,
               cache_key: str | None = None) -> dict:
        """Save the untouched original and the post-processed file; returns what `_register` needs."""
        post = DEFAULT_TTS_POST if body.post is None and not body.preset else body.post
        steps = audio_service.resolve_steps(post, body.preset)
        folder = subdir("audio", "generated")
        with clock("write"):
            original = au.save(unique_path(folder, "tts_original", "wav"), y, sr, ai_generated=True)
        path, out = original, y
        if steps:
            with clock("post"):
                out = audio_service.process_array(y, sr, steps)
            with clock("write"):
                path = au.save(unique_path(folder, "tts", "wav"), out, sr, ai_generated=True)
        return {"path": path, "original": original, "out": out, "sr": sr, "steps": steps,
                "label": body.name or (info["text"][:40] + ("…" if len(info["text"]) > 40 else "")),
                "params": {**info, "steps": steps, "preset": body.preset, "cache_key": cache_key}}

    def _register(self, session, saved: dict, timings: dict | None = None) -> dict:
        params = {**saved["params"], "timings": timings} if timings else saved["params"]
        audio = audio_service.register(
            session, saved["path"], AudioSource.GENERATED, name=saved["label"], ai_generated=True,
            original_path=saved["original"], params=params, y=saved["out"], sr=saved["sr"],
        )
        return audio_service.to_dict(audio)

    def _after_job(self) -> None:
        if system_service.get_setting("release_memory_after_job"):
            model_service.release_cached_memory()

    # ------------------------------------------------------------ public generation

    def generate(self, body: TTSRequest, progress: Progress | None = None) -> dict:
        """Generate, save original + processed files and create the audios record.

        With `body.cache`, an identical earlier request returns its audio (`cached: true`) instead.
        """
        try:
            clock = _Clock()
            cache_key = self.cache_key(body) if body.cache else None
            if cache_key:
                cached = audio_service.find_generated(cache_key)
                if cached:
                    logger.info(f"TTS request served from the cache (audio {cached['audios_id']})")
                    _report(progress, 1.0)
                    return {**cached, "cached": True, "timings": clock.report(cached["duration"])}
            y, sr, info = self._synthesize(body, clock, progress)
            saved = self._write(body, y, sr, info, clock, cache_key)
            _report(progress, 0.95, "Saving")
            with clock("database"), transaction() as session:
                result = self._register(session, saved, clock.report(au.duration(saved["out"], sr)))
            timings = clock.report(result["duration"])
            logger.info(f"Saved generated speech as audio {result['audios_id']} ({self.describe(timings)})")
            self._after_job()
            _report(progress, 1.0)
            return {**result, "cached": False, "timings": timings}
        except Exception as exc:
            raise service_error(exc, "tts_service.generate")

    @staticmethod
    def describe(timings: dict | None) -> str:
        """One line for people: audio length, time taken, real-time factor and where the time went."""
        if not timings:
            return ""
        parts = [f"{timings.get('audio_s', 0):.1f} s of audio in {timings.get('total_s', 0):.1f} s"]
        if timings.get("rtf") is not None:
            parts.append(f"RTF {timings['rtf']:.2f}")
        stages = [(label, timings.get(key)) for key, label in (
            ("queue_s", "queue"), ("load_s", "model load"), ("model_wait_s", "waiting for the model"),
            ("inference_s", "inference"), ("post_s", "post-processing"), ("write_s", "saving"))]
        details = ", ".join(f"{label} {value:.1f} s" for label, value in stages if value and value >= 0.05)
        return " · ".join(parts) + (f" ({details})" if details else "")

    def generate_async(self, body: TTSRequest) -> dict:
        try:
            Validation.require_text(body.text)  # report empty text immediately
            return job_service.submit(
                JobType.TTS,
                lambda ctx: self._job_result({"audio": self.generate(body, progress=ctx.progress)}, "audio"),
                title=f"Speech: {body.text.strip()[:40]}",
                params={"text": body.text[:200]},
            )
        except Exception as exc:
            raise service_error(exc, "tts_service.generate_async")

    @staticmethod
    def _job_result(result: dict, key: str) -> dict:
        """Lift the generation's timings to the job result, where JobService adds the queue time."""
        return {**result, "timings": dict(result[key].get("timings") or {})}

    def preview(self, body: TTSRequest, progress: Progress | None = None) -> dict:
        return self.generate(body.model_copy(update={"name": "Preview"}), progress=progress)

    def regenerate(self, body: RegenerateRequest, progress: Progress | None = None) -> dict:
        """Generate a fresh take with the same settings as an earlier generation."""
        try:
            source = audio_service.get(body.audios_id)
            params = dict(source["params"] or {})
            if "text" not in params:
                raise ValidationError("This audio was not generated from text", field="audios_id")
            keep = ("engine_voice", "speed", "pitch", "energy", "emotion", "style", "pause_ms", "pronunciations",
                    "temperature")
            request = TTSRequest(
                text=params["text"], voices_id=params.get("voices_id"), model_key=params.get("model_key"),
                post=params.get("steps"), name=source["name"], seed=body.seed,
                **{k: params[k] for k in keep if params.get(k) is not None},
            )
            logger.info(f"Regenerating audio {body.audios_id} (seed={body.seed})")
            return self.generate(request, progress=progress)
        except Exception as exc:
            raise service_error(exc, "tts_service.regenerate")

    def generate_sentences(self, body: TTSRequest, progress: Progress | None = None) -> dict:
        """One audio per sentence (for sentence-level regeneration) plus the joined result.

        `body.pause_ms` is the gap between sentences in the joined audio. The voice and model are resolved
        once and the sentences are spoken in order (batched on engines that batch); each still gets its own
        original, clean-up and audios record, exactly as a separate generation would.
        """
        try:
            sentences = split_sentences(Validation.require_text(body.text))
            gap_ms = PAUSE_SENTENCE_MS if body.pause_ms is None else body.pause_ms
            if body.cache:  # each sentence looks up its own earlier audio
                audios = []
                for index, sentence in enumerate(sentences):
                    audios.append(self.generate(body.model_copy(
                        update={"text": sentence, "name": f"Sentence {index + 1}", "pause_ms": None})))
                    _report(progress, (index + 1) / (len(sentences) + 1))
                combined = self.combine([a["audios_id"] for a in audios], gap_ms)
                return {"sentences": audios, "combined": combined}

            clock = _Clock()
            plan = self._plan(body.model_copy(update={"pause_ms": None}), clock, progress)
            spoken = self._speak(plan, sentences, clock, progress, span=(0.0, 0.85))
            saved = []
            for index, (sentence, (y, sr)) in enumerate(zip(sentences, spoken)):
                with clock("prosody"):
                    y, matched = self._shape(plan, y, sr)
                request = body.model_copy(update={"text": sentence, "name": f"Sentence {index + 1}", "pause_ms": None})
                info = {**plan.info, "text": sentence, "pitch_matched": matched}
                saved.append(self._write(request, y, sr, info, clock))
                _report(progress, 0.85 + 0.08 * (index + 1) / len(sentences), "Saving sentences")
            with clock("database"), transaction() as session:
                audios = [self._register(session, item) for item in saved]
            _report(progress, 0.95, "Joining sentences")
            combined = self.combine([a["audios_id"] for a in audios], gap_ms)
            timings = clock.report(combined["duration"], sentences=len(sentences))
            logger.info(f"Generated {len(sentences)} sentence(s) ({self.describe(timings)})")
            self._after_job()
            _report(progress, 1.0)
            return {"sentences": audios, "combined": combined, "timings": timings}
        except Exception as exc:
            raise service_error(exc, "tts_service.generate_sentences")

    def generate_sentences_async(self, body: TTSRequest) -> dict:
        try:
            Validation.require_text(body.text)
            return job_service.submit(
                JobType.TTS,
                lambda ctx: self.generate_sentences(body, progress=ctx.progress),
                title=f"Speech: {body.text.strip()[:40]}",
            )
        except Exception as exc:
            raise service_error(exc, "tts_service.generate_sentences_async")

    def regenerate_sentence(self, audios_ids: list[int], index: int, gap_ms: int = PAUSE_SENTENCE_MS,
                            progress=None) -> dict:
        """Regenerate one sentence of a per-sentence generation and rebuild the joined audio."""
        try:
            if not 0 <= index < len(audios_ids):
                raise ValidationError("Sentence index out of range", field="index")
            fresh = self.regenerate(RegenerateRequest(audios_id=audios_ids[index]), progress=progress)
            ids = list(audios_ids)
            ids[index] = fresh["audios_id"]
            return {"sentence": fresh, "combined": self.combine(ids, gap_ms), "timings": fresh.get("timings")}
        except Exception as exc:
            raise service_error(exc, "tts_service.regenerate_sentence")

    def regenerate_sentence_async(self, audios_ids: list[int], index: int, gap_ms: int = PAUSE_SENTENCE_MS) -> dict:
        try:
            return job_service.submit(
                JobType.TTS,
                lambda ctx: self.regenerate_sentence(audios_ids, index, gap_ms, progress=ctx.progress),
                title=f"Regenerate sentence {index + 1}",
            )
        except Exception as exc:
            raise service_error(exc, "tts_service.regenerate_sentence_async")

    def combine(self, audios_ids: list[int], gap_ms: int = PAUSE_SENTENCE_MS) -> dict:
        try:
            if len(audios_ids) == 1:
                return audio_service.get(audios_ids[0])
            return audio_service.join(audios_ids, gap_ms, name="Generated speech")
        except Exception as exc:
            raise service_error(exc, "tts_service.combine")


tts_service = TTSService()
