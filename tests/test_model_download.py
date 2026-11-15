"""Model weights can be downloaded even when the optional Python extra is not installed."""

from app.constants.models import MODEL_CATALOG

import urllib.error

import pytest

from app.exceptions import ModelError
from app.services import model_service as model_service_module
from app.services.model_service import model_service
from app.utils.model import download


def test_every_local_engine_has_weight_urls():
    by_key = {entry["key"]: entry for entry in MODEL_CATALOG}
    for key in ("piper-en-us-lessac-medium", "kokoro-82m", "chatterbox", "chatterbox-turbo", "qwen3-tts-0.6b"):
        files = by_key[key].get("files") or {}
        assert files, key
        assert all(url.startswith("https://huggingface.co/") for url in files.values())


def test_download_keeps_a_file_another_install_already_finished(monkeypatch, tmp_path):
    dest = tmp_path / "voice.pt"
    dest.write_bytes(b"weights")

    def refuse(*_args, **_kwargs):
        raise AssertionError("should not download a file that is already saved")

    monkeypatch.setattr("app.utils.model.urllib.request.urlopen", refuse)
    assert download("https://example.invalid/voice.pt", dest).read_bytes() == b"weights"


def test_download_reports_http_errors(monkeypatch, tmp_path):
    def refuse(request, timeout=0):
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", hdrs=None, fp=None)

    monkeypatch.setattr("app.utils.model.urllib.request.urlopen", refuse)
    with pytest.raises(ModelError, match="voice.bin"):
        download("https://example.invalid/voice.bin", tmp_path / "voice.bin")
    assert not (tmp_path / "voice.bin").exists()
    assert not (tmp_path / "voice.bin.part").exists()


def test_install_saves_weights_before_the_python_extra_is_installed(monkeypatch):
    entry = dict(model_service_module._CATALOG["fake-tts"])
    entry["files"] = {"voice.bin": "https://example.invalid/voice.bin"}
    entry["package"] = "no_such_voxlabs_pkg"
    entry["extra"] = "piper"
    model_service_module._CATALOG["fake-tts"] = entry

    def fake_download(url, dest, progress=None, cancelled=None):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"weights")
        if progress:
            progress(1)
        return dest

    monkeypatch.setattr(model_service_module, "download", fake_download)
    saved = model_service.install("fake-tts")
    assert saved["files_ready"] is True
    assert saved["installed"] is False
    assert (model_service.model_dir("fake-tts") / "voice.bin").read_bytes() == b"weights"


def test_install_still_requires_the_extra_when_there_are_no_files():
    entry = dict(model_service_module._CATALOG["fake-tts"])
    entry["package"] = "no_such_voxlabs_pkg"
    entry["extra"] = "kokoro"
    entry.pop("files", None)
    model_service_module._CATALOG["fake-tts"] = entry
    with pytest.raises(ModelError, match="uv sync --inexact --extra kokoro"):
        model_service.install("fake-tts")


def test_install_all_downloads_file_models_and_skips_the_rest(monkeypatch):
    catalog = dict(model_service_module._CATALOG)
    catalog["fake-tts"] = {
        **catalog["fake-tts"],
        "files": {"voice.bin": "https://example.invalid/voice.bin"},
        "package": "no_such_voxlabs_pkg",
        "extra": "piper",
    }
    catalog["fake-clone"] = {**catalog["fake-clone"], "package": "no_such_voxlabs_pkg", "extra": "chatterbox"}
    model_service_module._CATALOG = catalog
    original = model_service.list_models
    monkeypatch.setattr(model_service, "list_models",
                        lambda *args, **kwargs: [m for m in original() if m["key"].startswith("fake-")])

    def fake_download(url, dest, progress=None, cancelled=None):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"weights")
        return dest

    monkeypatch.setattr(model_service_module, "download", fake_download)
    result = model_service.install_all()
    assert [item["name"] for item in result["downloaded"]] == ["Fake TTS"]
    assert result["downloaded"][0]["ready"] is True
    assert result["failed"] == []
    assert result["skipped"] == [{"key": "fake-clone", "name": "Fake Clone", "reason": "close VoxLabs and run: uv sync --inexact --extra chatterbox"}]


def test_retired_engines_are_gone():
    """XTTS v2 and F5-TTS were removed: not in the catalog, and a database row left from them is hidden."""
    from app.constants.status import Status
    from app.models import Model
    from app.utils.database import transaction

    assert not {"xtts-v2", "f5-tts"} & {entry["key"] for entry in MODEL_CATALOG}
    with transaction() as session:
        session.add(Model(key="xtts-v2", name="Coqui XTTS v2", model_type="clone", backend="xtts", version="2",
                          size_mb=0, vram_mb=0, capabilities=[], online=False))
    model_service.sync_catalog()
    assert "xtts-v2" not in {model["key"] for model in model_service.list_models()}
    assert model_service.get("xtts-v2")["status"] == Status.DELETED.code


def test_chatterbox_watermarker_can_load():
    """Chatterbox and Chatterbox Turbo watermark their output with resemble-perth, which imports pkg_resources.
    setuptools 82 dropped it, which left perth's watermarker as None and neither model could start."""
    import warnings

    perth = pytest.importorskip("perth")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # pkg_resources warns that it is deprecated
        import importlib

        importlib.reload(perth)
    assert perth.PerthImplicitWatermarker is not None


def test_download_resumes_after_a_connection_interruption(monkeypatch, tmp_path):
    dest = tmp_path / "voice.bin"
    requests = []

    class Response:
        def __init__(self, chunks, status=200, headers=None):
            self.chunks = iter(chunks)
            self.status = status
            self.headers = headers or {}

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size):
            chunk = next(self.chunks)
            if isinstance(chunk, Exception):
                raise chunk
            return chunk

    def open_url(request, timeout=0):
        requests.append(request)
        if len(requests) == 1:
            return Response([b"abc", urllib.error.URLError("connection lost")])
        assert request.get_header("Range") == "bytes=3-"
        return Response([b"def", b""], status=206,
                        headers={"Content-Length": "3", "Content-Range": "bytes 3-5/6"})

    monkeypatch.setattr("app.utils.model.urllib.request.urlopen", open_url)

    assert download("https://example.invalid/voice.bin", dest).read_bytes() == b"abcdef"
    assert len(requests) == 2


def test_download_keeps_partial_file_when_cancelled(monkeypatch, tmp_path):
    dest = tmp_path / "voice.bin"

    class Response:
        status = 200
        headers = {"Content-Length": "6"}

        def __init__(self):
            self.chunks = iter([b"abc", b"def"])

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _size):
            return next(self.chunks, b"")

    monkeypatch.setattr("app.utils.model.urllib.request.urlopen", lambda *_args, **_kwargs: Response())
    calls = iter([False, True])

    with pytest.raises(ModelError, match="Download cancelled"):
        download("https://example.invalid/voice.bin", dest, cancelled=lambda: next(calls))

    assert list(tmp_path.glob("voice.bin.*.part"))
    assert not dest.exists()
