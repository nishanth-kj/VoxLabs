"""Build a one-folder desktop bundle with PyInstaller: `uv run python scripts/build.py`.

Output: dist/VoxLabs/ (Windows, Linux) or dist/VoxLabs.app (macOS). The app icon is rendered
from the same logo the app draws at runtime (app/ui/icons.py), as .ico on Windows and .icns
on macOS; Linux reads the window icon at runtime.
"""

import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "build" / "icon"


def _png(pixels: int) -> bytes:
    from PySide6.QtCore import QBuffer, QIODevice

    from app.ui.icons import logo_image

    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    logo_image(pixels).save(buffer, "PNG")
    return bytes(buffer.data())


def _write_ico(path: Path) -> Path:
    """A multi-size .ico with PNG entries (supported since Windows Vista)."""
    images = [(size, _png(size)) for size in (16, 24, 32, 48, 64, 128, 256)]
    offset = 6 + 16 * len(images)
    header = struct.pack("<HHH", 0, 1, len(images))
    entries, data = b"", b""
    for size, png in images:
        side = 0 if size >= 256 else size  # 0 means 256 in the ICO directory
        entries += struct.pack("<BBBBHHII", side, side, 0, 0, 1, 32, len(png), offset + len(data))
        data += png
    path.write_bytes(header + entries + data)
    return path


def _write_icns(path: Path) -> Path:
    iconset = ICON_DIR / "VoxLabs.iconset"
    iconset.mkdir(parents=True, exist_ok=True)
    for size in (16, 32, 128, 256, 512):
        (iconset / f"icon_{size}x{size}.png").write_bytes(_png(size))
        (iconset / f"icon_{size}x{size}@2x.png").write_bytes(_png(size * 2))
    subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(path)], check=True)
    return path


def app_icon_file() -> Path | None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    sys.path.insert(0, str(ROOT))
    from PySide6.QtGui import QGuiApplication

    _app = QGuiApplication.instance() or QGuiApplication([])  # noqa: F841 - SVG rendering needs one
    shutil.rmtree(ICON_DIR, ignore_errors=True)
    ICON_DIR.mkdir(parents=True)
    if sys.platform == "win32":
        return _write_ico(ICON_DIR / "VoxLabs.ico")
    if sys.platform == "darwin":
        return _write_icns(ICON_DIR / "VoxLabs.icns")
    return None


def main() -> int:
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name", "VoxLabs",
        "--paths", str(ROOT),
        "--collect-data", "librosa",
        "--collect-submodules", "app",
    ]
    icon = app_icon_file()
    if icon:
        command += ["--icon", str(icon)]
    if sys.platform == "darwin":
        command += ["--osx-bundle-identifier", "app.voxlabs.desktop"]
    command.append(str(ROOT / "app" / "main.py"))
    print(" ".join(command))
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
