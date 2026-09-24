"""Shared fixtures: an isolated data directory per test and an offline fake TTS engine."""

import numpy as np
import pytest

from app.constants.models import ModelType
from app.services import model_service as model_service_module
from app.services.job_service import job_service
from app.services.model_service import model_service
from app.services.system_service import system_service
from app.utils import audio as au
from app.utils.database import reset_engine
from app.utils.model import ModelBackend, register_backend

FAKE_SR = 16000


class FakeBackend(ModelBackend):
    """Deterministic offline 'speech': a 180 Hz tone, 60 ms per character."""

    backend_id = "fake"

    def synthesize(self, request, voice):
        seconds = max(0.3, 0.06 * len(request.text))
        t = np.arange(int(seconds * FAKE_SR)) / FAKE_SR
        y = 0.3 * np.sin(2 * np.pi * 180 * t) + 0.1 * np.sin(2 * np.pi * 360 * t)
        return y.astype(np.float32), FAKE_SR


class FakeCloneBackend(FakeBackend):
    backend_id = "fakeclone"
    supports_cloning = True

    def synthesize(self, request, voice):
        self._require_reference(voice)
        return super().synthesize(request, voice)


FAKE_MODELS = [
    {"key": "fake-tts", "name": "Fake TTS", "model_type": ModelType.TTS, "backend": "fake", "version": "1",
     "size_mb": 0, "vram_mb": 0, "online": False, "package": None, "extra": None, "capabilities": ["tts"]},
    {"key": "fake-clone", "name": "Fake Clone", "model_type": ModelType.CLONE, "backend": "fakeclone",
     "version": "1", "size_mb": 0, "vram_mb": 0, "online": False, "package": None, "extra": None,
     "capabilities": ["tts", "clone"]},
]


@pytest.fixture(autouse=True)
def app_env(tmp_path, monkeypatch):
    monkeypatch.setenv("VOXLABS_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.delenv("VOXLABS_API_TOKEN", raising=False)
    catalog = model_service_module.MODEL_CATALOG + FAKE_MODELS
    monkeypatch.setattr(model_service_module, "MODEL_CATALOG", catalog)
    monkeypatch.setattr(model_service_module, "_CATALOG", {m["key"]: m for m in catalog})
    register_backend("fake", FakeBackend)
    register_backend("fakeclone", FakeCloneBackend)
    reset_engine()
    system_service.reset_cache()
    system_service.initialize()
    system_service.update_settings(default_tts_model="fake-tts")
    yield tmp_path
    job_service.shutdown(wait=True)
    model_service.unload_all()
    reset_engine()
    system_service.reset_cache()


def make_voice_wav(path, seconds: float = 4.0, sr: int = 24000, f0: float = 140.0, noise: float = 0.01):
    """A voiced-sounding test sample: harmonics with gentle amplitude modulation and noise."""
    rng = np.random.default_rng(0)
    t = np.arange(int(seconds * sr)) / sr
    y = sum(np.sin(2 * np.pi * f0 * k * t) / k for k in range(1, 6))
    y = 0.25 * y * (0.6 + 0.4 * np.sin(2 * np.pi * 3 * t)) + noise * rng.standard_normal(t.size)
    au.save(path, y.astype(np.float32), sr)
    return path


@pytest.fixture
def voice_wav(tmp_path):
    return make_voice_wav(tmp_path / "speaker.wav")


@pytest.fixture
def consent():
    return {"confirmed": True, "granted_by": "Test Operator", "speaker_name": "Test Speaker"}
