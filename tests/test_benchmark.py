"""Tests for reproducible benchmark metadata."""

from importlib import metadata

from scripts import benchmark


def test_package_version_returns_installed_version(monkeypatch):
    monkeypatch.setattr(benchmark.importlib.metadata, "version", lambda name: "2.6.0")

    assert benchmark.package_version("torch") == "2.6.0"


def test_package_version_returns_none_when_runtime_is_missing(monkeypatch):
    def missing(_name):
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(benchmark.importlib.metadata, "version", missing)

    assert benchmark.package_version("torch") is None


def test_package_version_uses_distribution_name_for_piper(monkeypatch):
    requested = []
    monkeypatch.setattr(benchmark.importlib.metadata, "version", lambda name: requested.append(name) or "1.2.0")

    assert benchmark.package_version("piper") == "1.2.0"
    assert requested == ["piper-tts"]


def test_package_version_uses_distribution_name_for_chatterbox(monkeypatch):
    requested = []
    monkeypatch.setattr(benchmark.importlib.metadata, "version", lambda name: requested.append(name) or "0.1.7")

    assert benchmark.package_version("chatterbox") == "0.1.7"
    assert requested == ["chatterbox-tts"]
