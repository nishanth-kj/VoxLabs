"""The desktop build: package names and where a built app keeps its data."""

import importlib.util
import runpy
import sys
from pathlib import Path

import pytest

from app.utils import files

ROOT = Path(__file__).resolve().parents[1]


def _build_script():
    spec = importlib.util.spec_from_file_location("voxlabs_build", ROOT / "scripts" / "build.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_package_and_installer_names_match_the_release_assets():
    """The site's download hints name exactly these files (the portable package comes first)."""
    build = _build_script()
    assert build.artifact_names("win32", "AMD64") == [
        "VoxLabs-Windows-x64.zip", "VoxLabs-Windows-x64-Setup.exe", "VoxLabs-Windows-x64.msi"]
    assert build.artifact_names("darwin", "arm64") == ["VoxLabs-macOS-arm64.dmg", "VoxLabs-macOS-arm64.pkg"]
    assert build.artifact_names("linux", "x86_64") == [
        "VoxLabs-Linux-x86_64.tar.gz", "VoxLabs-Linux-x86_64.deb", "VoxLabs-Linux-x86_64.rpm"]
    links = (ROOT / "site" / "lib" / "links.ts").read_text(encoding="utf-8")
    for name in ("VoxLabs-Windows-x64-Setup.exe", "VoxLabs-macOS-arm64.dmg", "VoxLabs-Linux-x86_64.deb"):
        assert name in links
    workflow = (ROOT / ".github" / "workflows" / "desktop.yml").read_text(encoding="utf-8")
    assert "uv run build --require-installers" in workflow and "dist/VoxLabs-*" in workflow


def test_bundle_includes_what_engines_read_at_runtime(monkeypatch):
    """Chatterbox fails to load without Perth's watermark checkpoint (package data), and the app sets up
    Qwen3-TTS's environment with a bundled uv and runs the worker script from the bundle."""
    build = _build_script()
    commands = []
    monkeypatch.setattr(build, "app_icon_file", lambda: None)
    monkeypatch.setattr(build.subprocess, "call", lambda command, **_kwargs: commands.append(command) or 0)
    monkeypatch.setattr(build.importlib.util, "find_spec", lambda _name: object())  # chatterbox installed
    monkeypatch.setenv("UV", str(ROOT / "uv-binary"))
    assert build.bundle() == 0
    command = commands[0]
    assert command[command.index("perth") - 1] == "--collect-data"
    assert f"{ROOT / 'uv-binary'}{build.os.pathsep}." in command
    assert any(arg.endswith("app/utils/engine_workers") for arg in command)


def test_built_app_keeps_data_in_the_user_folder(monkeypatch, tmp_path):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert files.default_data_dir() == files.PROJECT_ROOT / "data"  # from source: ./data

    monkeypatch.setattr(sys, "frozen", True, raising=False)  # what PyInstaller sets
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    expected = Path.home() / "Library" / "Application Support" if sys.platform == "darwin" else tmp_path
    assert files.default_data_dir() == expected / "VoxLabs"


def test_windowed_app_gets_std_streams(monkeypatch):
    """A windowed build starts with sys.stdout/stderr = None; libraries that print (Kokoro) then crash."""
    import app.main as entry

    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)
    entry._ensure_std_streams()
    out, err = sys.stdout, sys.stderr
    assert out is not None and err is not None
    try:
        print("discarded")
        err.write("discarded\n")
    finally:
        out.close()
        err.close()


def test_self_test_crash_reports_and_exits_without_a_windowed_error_dialog(monkeypatch, tmp_path):
    from app.services.system_service import system_service

    def fail():
        raise RuntimeError("bundled dependency missing")

    report = tmp_path / "crash.txt"
    monkeypatch.setenv("VOXLABS_CRASH_REPORT", str(report))
    monkeypatch.setattr(sys, "argv", ["VoxLabs", "--self-test"])
    monkeypatch.setattr(system_service, "initialize", fail)
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(ROOT / "app" / "main.py"), run_name="__main__")
    assert exc.value.code == 1
    assert "RuntimeError: bundled dependency missing" in report.read_text(encoding="utf-8")
