"""Build a one-folder desktop bundle with PyInstaller: `uv run python scripts/build.py`."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--name", "VoxLabs",
        "--paths", str(ROOT),
        "--collect-data", "librosa",
        "--collect-submodules", "app",
        str(ROOT / "app" / "main.py"),
    ]
    print(" ".join(command))
    return subprocess.call(command, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
