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
    for key in ("piper-en-us-lessac-medium", "kokoro-82m", "xtts-v2", "f5-tts", "chatterbox"):
        files = by_key[key].get("files") or {}
        assert files, key
        assert all(url.startswith("https://huggingface.co/") for url in files.values())


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
    with pytest.raises(ModelError, match="uv sync --extra kokoro"):
        model_service.install("fake-tts")


def test_install_all_downloads_file_models_and_skips_the_rest(monkeypatch):
    catalog = dict(model_service_module._CATALOG)
    catalog["fake-tts"] = {
        **catalog["fake-tts"],
        "files": {"voice.bin": "https://example.invalid/voice.bin"},
        "package": "no_such_voxlabs_pkg",
        "extra": "piper",
    }
    catalog["fake-clone"] = {**catalog["fake-clone"], "package": "no_such_voxlabs_pkg", "extra": "f5"}
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
    assert result["skipped"] == [{"key": "fake-clone", "name": "Fake Clone", "reason": "run uv sync --extra f5"}]
