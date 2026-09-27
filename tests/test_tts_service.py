from pathlib import Path

import pytest

from app.constants.audio import AI_GENERATED_TAG
from app.exceptions import ModelError, ValidationError
from app.models.request import RegenerateRequest, TTSRequest
from app.services import model_service as model_service_module
from app.services.clone_service import clone_service
from app.services.model_service import model_service
from app.services.system_service import system_service
from app.services.tts_service import _chunks, apply_pronunciations, split_sentences, tts_service
from app.utils import audio as au
from app.utils.model import register_backend
from tests.conftest import FakeBackend


def test_split_sentences_and_pause_tags():
    assert split_sentences("Hello there. How are you? Fine!\n\nNew paragraph.") == [
        "Hello there.", "How are you?", "Fine!", "New paragraph."]
    chunks = _chunks("One. [pause 2s] Two.")
    assert chunks[0] == ("One.", 2000) and chunks[1][0] == "Two."


def test_pronunciations():
    assert apply_pronunciations("Use SQL daily", {"SQL": "sequel"}) == "Use sequel daily"


def test_generate_creates_labeled_audio_with_original_kept():
    audio = tts_service.generate(TTSRequest(text="Hello world. This is VoxLabs."))
    assert audio["ai_generated"] is True and audio["label"] == AI_GENERATED_TAG
    assert audio["source"] == "generated"
    assert Path(audio["original_path"]).exists() and audio["original_path"] != audio["path"]
    assert audio["params"]["model_key"] == "fake-tts"
    assert au.read_tags(audio["path"]).get("comment") == AI_GENERATED_TAG


def test_speed_changes_duration():
    normal = tts_service.generate(TTSRequest(text="Speed test sentence.", post={}))
    fast = tts_service.generate(TTSRequest(text="Speed test sentence.", post={}, speed=2.0))
    assert fast["duration"] < normal["duration"] * 0.6


def test_validation_errors():
    with pytest.raises(ValidationError):
        tts_service.generate(TTSRequest(text="   "))
    with pytest.raises(ValidationError):
        tts_service.generate(TTSRequest(text="Hi", speed=5))
    with pytest.raises(ValidationError):
        tts_service.generate(TTSRequest(text="Hi", emotion="furious"))


def test_online_models_are_opt_in():
    with pytest.raises(ModelError, match="online"):
        tts_service.generate(TTSRequest(text="Hi", model_key="gtts-emotional"))
    system_service.update_settings(allow_online_models=True)
    assert model_service.get("gtts-emotional")["allowed"]


def test_regenerate_and_sentences():
    first = tts_service.generate(TTSRequest(text="Regenerate me.", seed=1))
    again = tts_service.regenerate(RegenerateRequest(audios_id=first["audios_id"], seed=2))
    assert again["params"]["text"] == "Regenerate me." and again["params"]["seed"] == 2
    result = tts_service.generate_sentences(TTSRequest(text="One. Two. Three."))
    assert len(result["sentences"]) == 3
    assert result["combined"]["duration"] > sum(s["duration"] for s in result["sentences"])


def test_clone_voice_with_cloning_model_and_fallback(voice_wav, consent):
    voice = clone_service.clone([voice_wav], "Cloned", consent, model_key="fake-clone")
    cloned = tts_service.generate(TTSRequest(text="Speak in my voice.", voices_id=voice["voices_id"]))
    assert cloned["params"]["model_key"] == "fake-clone" and cloned["params"]["cloned"] is True
    profile_voice = clone_service.clone([voice_wav], "Profile", consent)
    matched = tts_service.generate(TTSRequest(text="Approximate my voice.", voices_id=profile_voice["voices_id"]))
    assert matched["params"]["model_key"] == "fake-tts" and matched["params"]["cloned"] is False
    # A speaking voice stays on its own model even if the request names another one.
    stuck = tts_service.generate(TTSRequest(
        text="Stay on the clone model.", voices_id=voice["voices_id"], model_key="fake-tts"))
    assert stuck["params"]["model_key"] == "fake-clone"


def test_chunks_follow_the_engine_limit():
    text = "First sentence here. Second sentence here. Third sentence here."
    assert len(_chunks(text)) == 1
    assert [c for c, _ in _chunks(text, max_chars=45)] == [
        "First sentence here. Second sentence here.", "Third sentence here."]


def test_cache_returns_the_earlier_audio():
    first = tts_service.generate(TTSRequest(text="Cache me once.", cache=True))
    again = tts_service.generate(TTSRequest(text="Cache me once.", cache=True, name="Other label"))
    assert first["cached"] is False and again["cached"] is True
    assert again["audios_id"] == first["audios_id"]
    different = tts_service.generate(TTSRequest(text="Cache me once.", cache=True, speed=1.5))
    assert different["audios_id"] != first["audios_id"]
    uncached = tts_service.generate(TTSRequest(text="Cache me once."))
    assert uncached["audios_id"] != first["audios_id"] and uncached["cached"] is False


def test_engine_voice_reaches_the_backend():
    seen = []

    class RecordingBackend(FakeBackend):
        def synthesize(self, request, voice):
            seen.append(voice.engine_voice if voice else None)
            return super().synthesize(request, voice)

    register_backend("fake", RecordingBackend)
    audio = tts_service.generate(TTSRequest(text="Pick a built-in voice.", engine_voice="af_bella"))
    assert seen == ["af_bella"] and audio["params"]["engine_voice"] == "af_bella"
    with pytest.raises(ValidationError):
        tts_service.generate(TTSRequest(text="Hi", engine_voice="not a voice!"))


def test_falls_back_to_an_installed_model(monkeypatch):
    monkeypatch.setattr(model_service_module, "FALLBACK_TTS_MODELS", ("chatterbox-turbo", "fake-tts"))
    system_service.update_settings(default_tts_model="piper-en-us-lessac-medium")  # not installed in tests
    audio = tts_service.generate(TTSRequest(text="Fallback please."))
    assert audio["params"]["model_key"] == "fake-tts"
    with pytest.raises(ModelError, match="not downloaded|engine"):
        tts_service.generate(TTSRequest(text="Explicit model.", model_key="piper-en-us-lessac-medium"))


def test_gpu_out_of_memory_loads_on_cpu(monkeypatch):
    class OutOfMemoryError(RuntimeError):
        pass

    class GreedyBackend(FakeBackend):
        def load(self):
            if self.device.startswith("cuda"):
                raise OutOfMemoryError("CUDA out of memory")
            super().load()

    register_backend("fake", GreedyBackend)
    monkeypatch.setattr(model_service, "pick_device", lambda model, requested=None: "cuda:0")
    assert model_service.load("fake-tts")["loaded_device"] == "cpu"
