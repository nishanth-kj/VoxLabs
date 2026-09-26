"""The desktop build: package names and where a built app keeps its data."""

import importlib.util
import sys
from pathlib import Path

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


def test_built_app_keeps_data_in_the_user_folder(monkeypatch, tmp_path):
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert files.default_data_dir() == files.PROJECT_ROOT / "data"  # from source: ./data

    monkeypatch.setattr(sys, "frozen", True, raising=False)  # what PyInstaller sets
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    expected = Path.home() / "Library" / "Application Support" if sys.platform == "darwin" else tmp_path
    assert files.default_data_dir() == expected / "VoxLabs"
