"""Engines in their own environment (Qwen3-TTS): setup, install status and the helper-process protocol.

The helper here is a fake worker run with this interpreter, so the suite never needs the real engine."""

import ast
import json
import sys
import textwrap
from pathlib import Path

import numpy as np
import pytest

from app.constants.models import ENGINE_ENVIRONMENTS, MODEL_CATALOG
from app.exceptions import ModelError
from app.services import model_service as model_service_module
from app.services.model_service import model_service
from app.utils import model as model_utils
from app.utils.model import Qwen3Backend, SynthesisRequest, VoiceRef, environment_dir, environment_ready

def _write_worker(path: Path) -> Path:
    # Mirrors the real worker's protocol: ready line, then one reply per request.
    path.write_text(textwrap.dedent('''
        import base64, json, sys
        import numpy as np

        reply, sys.stdout = sys.stdout, sys.stderr
        print("library banner goes to stderr")

        def send(message):
            reply.write(json.dumps(message) + "\\n")
            reply.flush()

        send({"ready": True, "device": "cpu"})
        for line in sys.stdin:
            request = json.loads(line)
            if request["text"] == "fail":
                send({"error": "the engine refused"})
                continue
            audio = np.full(len(request["text"]) * 100, 0.25, dtype="<f4")
            send({"audio": base64.b64encode(audio.tobytes()).decode("ascii"), "sr": 24000,
                  "echo": request})
    '''), encoding="utf-8")
    return path


@pytest.fixture
def fake_environment(monkeypatch, tmp_path):
    """The qwen3-tts environment, with this interpreter as its Python and a fake worker script."""
    worker = _write_worker(tmp_path / "fake_worker.py")
    spec = dict(ENGINE_ENVIRONMENTS["qwen3-tts"], worker=str(worker))
    monkeypatch.setitem(ENGINE_ENVIRONMENTS, "qwen3-tts", spec)
    monkeypatch.setattr(model_utils, "environment_python", lambda _name: Path(sys.executable))
    folder = environment_dir("qwen3-tts")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "voxlabs-environment.json").write_text(json.dumps({"requirements": list(spec["requirements"])}))
    return folder


def test_qwen3_is_in_the_catalog_with_its_own_environment():
    entry = {e["key"]: e for e in MODEL_CATALOG}["qwen3-tts-0.6b"]
    assert entry["environment"] in ENGINE_ENVIRONMENTS
    assert entry["package"] is None and entry["extra"] is None
    assert all(url.startswith("https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base/") for url in entry["files"].values())
    assert "speech_tokenizer/model.safetensors" in entry["files"]


def test_the_worker_script_does_not_import_the_app():
    """The worker runs with the engine's Python, where VoxLabs' packages are not installed."""
    for name in {spec["worker"] for spec in ENGINE_ENVIRONMENTS.values()}:
        source = (Path(model_utils.__file__).parent / "engine_workers" / name).read_text(encoding="utf-8")
        for node in ast.walk(ast.parse(source)):
            modules = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            assert not any(m == "app" or m.startswith("app.") for m in modules), name


def test_environment_is_ready_only_with_the_current_requirements(fake_environment):
    assert environment_ready("qwen3-tts")
    (fake_environment / "voxlabs-environment.json").write_text(json.dumps({"requirements": ["qwen-tts==0.0.1"]}))
    assert not environment_ready("qwen3-tts")
    (fake_environment / "voxlabs-environment.json").unlink()
    assert not environment_ready("qwen3-tts")
    assert environment_ready(None)


def test_worker_backend_speaks_through_its_helper_process(fake_environment, voice_wav, tmp_path):
    backend = Qwen3Backend(tmp_path / "weights", "cuda:0")
    backend.load()
    try:
        assert backend.loaded and backend.device == "cpu"  # the worker reports the device it really used
        voice = VoiceRef(sample_paths=[str(voice_wav)], language="de")
        audio, sr = backend.synthesize(SynthesisRequest(text="Hallo", temperature=0.7, seed=3), voice)
        assert sr == 24000 and audio.dtype == np.float32 and audio.size == 500
        assert np.allclose(audio, 0.25)
        with pytest.raises(ModelError, match="the engine refused"):
            backend.synthesize(SynthesisRequest(text="fail"), voice)
        audio, _ = backend.synthesize(SynthesisRequest(text="still alive"), voice)  # an error keeps it running
        assert audio.size == 1100
        with pytest.raises(ModelError, match="only speaks in a cloned voice"):
            backend.synthesize(SynthesisRequest(text="Hi"), None)
    finally:
        backend.unload()
    assert not backend.loaded and backend._process is None


def test_worker_backend_refuses_to_load_before_setup(tmp_path):
    with pytest.raises(ModelError, match="not set up yet"):
        Qwen3Backend(tmp_path, "cpu").load()


def test_install_downloads_weights_and_sets_up_the_environment(monkeypatch):
    created = []

    def fake_download(url, dest, progress=None, cancelled=None):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"weights")
        return dest

    def fake_create(name, cancelled=None):
        created.append(name)
        folder = environment_dir(name)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "voxlabs-environment.json").write_text(
            json.dumps({"requirements": list(ENGINE_ENVIRONMENTS[name]["requirements"])}))

    monkeypatch.setattr(model_service_module, "download", fake_download)
    monkeypatch.setattr(model_utils, "environment_python", lambda _name: Path(sys.executable))
    assert model_service.get("qwen3-tts-0.6b")["install_label"] == "Not downloaded"
    monkeypatch.setattr(model_service_module, "create_environment", lambda name, cancelled=None: None)
    model = model_service.install("qwen3-tts-0.6b")  # weights saved, environment setup did nothing
    assert not model["installed"] and model["files_ready"]
    assert model["install_label"] == "Downloaded · engine not set up (Install sets it up)"
    with pytest.raises(ModelError, match="not set up yet"):
        model_service.resolve_speech_model("qwen3-tts-0.6b")

    monkeypatch.setattr(model_service_module, "create_environment", fake_create)
    model = model_service.install("qwen3-tts-0.6b")
    assert created == ["qwen3-tts"]
    assert model["installed"] and model["install_label"] == "Installed" and model["supports_cloning"]


def test_a_built_app_skips_engines_it_cannot_set_up(monkeypatch):
    original = model_service.list_models
    monkeypatch.setattr(model_service, "list_models",
                        lambda *args, **kwargs: [m for m in original() if m["key"] == "qwen3-tts-0.6b"])
    monkeypatch.setattr(model_service_module, "environment_supported", lambda: False)

    def refuse(*_args, **_kwargs):
        raise AssertionError("a built app must not try to install it")

    monkeypatch.setattr(model_service, "install", refuse)
    result = model_service.install_all()
    assert result == {"downloaded": [], "failed": [], "skipped": [
        {"key": "qwen3-tts-0.6b", "name": "Qwen3-TTS 0.6B",
         "reason": "this copy of VoxLabs cannot set up its engine environment"}]}
    assert model_service.get("qwen3-tts-0.6b")["install_label"] == "Not downloaded"


def test_create_environment_needs_uv_from_source(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    with pytest.raises(ModelError, match="source checkout"):
        model_utils.create_environment("qwen3-tts")
