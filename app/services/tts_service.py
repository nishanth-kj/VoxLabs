"""TTSService: text → speech with a chosen voice and model, then clean-up.

Flow: validate → resolve voice → resolve model → synthesize (chunked) →
shape prosody → save the untouched original → post-process → audios record.
"""

import re
from collections.abc import Callable

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
from app.exceptions import ValidationError
from app.services.audio_service import audio_service
from app.services.job_service import job_service
from app.services.model_service import model_service
from app.services.voice_service import CLONE, voice_service
from app.utils import audio as au
from app.utils.database import transaction
from app.utils.files import subdir, unique_path
from app.utils.logger import logger
from app.utils.model import SynthesisRequest, apply_prosody
from app.utils.validation import in_range, require_choice, require_emotion, require_text

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


def _chunks(text: str) -> list[tuple[str, int]]:
    """(text, pause_after_ms) chunks no longer than TTS_CHUNK_CHARS, honouring [pause N] tags."""
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
            if current and len(current) + len(sentence) + 1 > TTS_CHUNK_CHARS:
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


class TTSService:
    def synthesize(
        self,
        text: str,
        voices_id: int | None = None,
        model_key: str | None = None,
        *,
        speed: float = 1.0,
        pitch: float = 1.0,
        energy: float = 1.0,
        emotion: str = "neutral",
        style: str = "default",
        pause_ms: int | None = None,
        pronunciations: dict[str, str] | None = None,
        temperature: float | None = None,
        seed: int | None = None,
        progress: Callable[[float], None] | None = None,
    ) -> tuple[np.ndarray, int, dict]:
        """Generate raw speech in memory. Returns (audio, sample_rate, generation info)."""
        text = require_text(text)
        speed = in_range(speed, 0.5, 2.0, "speed", 1.0)
        pitch = in_range(pitch, 0.5, 2.0, "pitch", 1.0)
        energy = in_range(energy, 0.1, 2.0, "energy", 1.0)
        emotion = require_emotion(emotion)
        style = require_choice(style or "default", STYLE_PRESETS, "style")
        if temperature is not None:
            temperature = in_range(temperature, 0.1, 1.5, "temperature", 0.7)

        voice_ref, voice = (None, None)
        if voices_id:
            voice_ref, voice = voice_service.voice_ref(voices_id)
        model = model_service.resolve_speech_model(model_key, voice)
        backend = model_service.backend_for(model["key"])
        native = backend.native_params
        cloned = bool(voice and voice["source"] == CLONE and backend.supports_cloning)

        # Combine style and emotion presets with the explicit settings.
        style_preset = STYLE_PRESETS[style]
        emotion_preset = EMOTIONS["neutral"] if "emotion" in native else EMOTIONS[emotion]
        eff_speed = speed * style_preset["speed"] * emotion_preset["speed"]
        eff_pitch = pitch * emotion_preset["pitch"]
        eff_energy = energy * emotion_preset["energy"]
        gap_ms = max(0, (PAUSE_SENTENCE_MS if pause_ms is None else pause_ms) + style_preset["pause_ms"])

        request = SynthesisRequest(
            text="", language=(voice or {}).get("language") or "en", speed=eff_speed if "speed" in native else 1.0,
            pitch=eff_pitch if "pitch" in native else 1.0, emotion=emotion, style=style,
            temperature=temperature, seed=seed,
        )
        chunks = _chunks(apply_pronunciations(text, pronunciations))
        parts: list[np.ndarray] = []
        sr = 0
        for index, (chunk, pause_after) in enumerate(chunks):
            request.text = chunk
            y, chunk_sr = backend.synthesize(request, voice_ref)
            if sr and chunk_sr != sr:
                y = au.resample(y, chunk_sr, sr)
            sr = sr or chunk_sr
            parts.append(au.to_mono(y).astype(np.float32))
            parts.append(au.silence((gap_ms if pause_after < 0 else pause_after) / 1000, sr))
            if progress:
                progress((index + 1) / len(chunks) * 0.8)
        y = au.concat(parts[:-1])

        # Approximate a cloned voice's pitch on engines that cannot clone.
        pitch_match = 1.0
        if voice and voice["source"] == CLONE and not backend.supports_cloning and voice_ref.pitch_hz:
            generated = au.estimate_pitch_hz(y, sr)
            if generated:
                pitch_match = float(np.clip(voice_ref.pitch_hz / generated, 0.6, 1.6))

        y = apply_prosody(
            y, sr,
            speed=1.0 if "speed" in native else eff_speed,
            pitch=(1.0 if "pitch" in native else eff_pitch) * pitch_match,
            energy=eff_energy,
        )
        if progress:
            progress(0.9)
        info = {
            "text": text,
            "voices_id": voices_id,
            "voice_name": voice["name"] if voice else None,
            "model_key": model["key"],
            "online": model["online"],
            "cloned": cloned,
            "pitch_matched": pitch_match != 1.0,
            "speed": speed, "pitch": pitch, "energy": energy, "emotion": emotion, "style": style,
            "pause_ms": pause_ms, "pronunciations": pronunciations or {},
            "temperature": temperature, "seed": seed,
        }
        logger.info(f"TTS generated {au.duration(y, sr):.1f}s with {model['key']} (voice={voices_id})")
        return y, sr, info

    def generate(
        self,
        text: str,
        voices_id: int | None = None,
        model_key: str | None = None,
        *,
        post: dict | None = None,
        preset: str | None = None,
        projects_id: int | None = None,
        name: str | None = None,
        progress: Callable[[float], None] | None = None,
        **params,
    ) -> dict:
        """Generate, save original + processed files and create the audios record."""
        y, sr, info = self.synthesize(text, voices_id, model_key, progress=progress, **params)
        steps = audio_service.resolve_steps(DEFAULT_TTS_POST if post is None and not preset else post, preset)
        label = name or (info["text"][:40] + ("…" if len(info["text"]) > 40 else ""))
        folder = subdir("audio", "generated")
        original = au.save(unique_path(folder, "tts_original", "wav"), y, sr, ai_generated=True)
        path, out = original, y
        if steps:
            out = audio_service.process_array(y, sr, steps)
            path = au.save(unique_path(folder, "tts", "wav"), out, sr, ai_generated=True)
        with transaction() as session:
            audio = audio_service.register(
                session, path, AudioSource.GENERATED, name=label, ai_generated=True, original_path=original,
                params={**info, "steps": steps, "preset": preset}, projects_id=projects_id, y=out, sr=sr,
            )
            result = audio_service.to_dict(audio)
        if progress:
            progress(1.0)
        return result

    def generate_async(self, text: str, **kwargs) -> dict:
        return job_service.submit(
            JobType.TTS,
            lambda ctx: {"audio": self.generate(text, progress=ctx.progress, **kwargs)},
            title=f"Speech: {text.strip()[:40]}",
            params={"text": text[:200]},
        )

    def preview(self, text: str, **kwargs) -> dict:
        return self.generate(text, name="Preview", **kwargs)

    def regenerate(self, audios_id: int, seed: int | None = None, progress=None) -> dict:
        """Generate a fresh take with the same settings as an earlier generation."""
        source = audio_service.get(audios_id)
        params = dict(source["params"] or {})
        if "text" not in params:
            raise ValidationError("This audio was not generated from text", field="audios_id")
        keep = ("speed", "pitch", "energy", "emotion", "style", "pause_ms", "pronunciations", "temperature")
        return self.generate(
            params["text"], params.get("voices_id"), params.get("model_key"),
            post=params.get("steps"), projects_id=source["projects_id"], name=source["name"], seed=seed,
            progress=progress, **{k: params[k] for k in keep if k in params},
        )

    def generate_sentences(self, text: str, gap_ms: int = PAUSE_SENTENCE_MS, progress=None, **kwargs) -> dict:
        """One audio per sentence (for sentence-level regeneration) plus the joined result."""
        sentences = split_sentences(require_text(text))
        audios = []
        for index, sentence in enumerate(sentences):
            audios.append(self.generate(sentence, name=f"Sentence {index + 1}", **kwargs))
            if progress:
                progress((index + 1) / (len(sentences) + 1))
        combined = self.combine([a["audios_id"] for a in audios], gap_ms, projects_id=kwargs.get("projects_id"))
        return {"sentences": audios, "combined": combined}

    def generate_sentences_async(self, text: str, **kwargs) -> dict:
        return job_service.submit(
            JobType.TTS,
            lambda ctx: self.generate_sentences(text, progress=ctx.progress, **kwargs),
            title=f"Speech: {text.strip()[:40]}",
        )

    def regenerate_sentence(self, audios_ids: list[int], index: int, gap_ms: int = PAUSE_SENTENCE_MS,
                            projects_id: int | None = None, progress=None) -> dict:
        """Regenerate one sentence of a per-sentence generation and rebuild the joined audio."""
        if not 0 <= index < len(audios_ids):
            raise ValidationError("Sentence index out of range", field="index")
        fresh = self.regenerate(audios_ids[index], progress=progress)
        ids = list(audios_ids)
        ids[index] = fresh["audios_id"]
        return {"sentence": fresh, "combined": self.combine(ids, gap_ms, projects_id)}

    def regenerate_sentence_async(self, audios_ids: list[int], index: int, gap_ms: int = PAUSE_SENTENCE_MS,
                                  projects_id: int | None = None) -> dict:
        return job_service.submit(
            JobType.TTS,
            lambda ctx: self.regenerate_sentence(audios_ids, index, gap_ms, projects_id, progress=ctx.progress),
            title=f"Regenerate sentence {index + 1}",
        )

    def combine(self, audios_ids: list[int], gap_ms: int = PAUSE_SENTENCE_MS, projects_id: int | None = None) -> dict:
        if len(audios_ids) == 1:
            return audio_service.get(audios_ids[0])
        return audio_service.join(audios_ids, gap_ms, name="Generated speech", projects_id=projects_id)


tts_service = TTSService()
