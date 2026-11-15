"""The base application must not import optional speech-engine runtimes at startup."""

import subprocess
import sys
from pathlib import Path


def test_model_service_startup_does_not_import_optional_engine_runtimes():
    """Importing the model service must work without importing any engine's heavy runtime."""
    root = Path(__file__).resolve().parents[1]
    check = """
import sys
import app.services.model_service
blocked = (
    "torch",
    "torchaudio",
    "kokoro",
    "piper",
    "chatterbox",
    "qwen_tts",
    "transformers",
)
loaded = sorted(
    name for name in sys.modules
    if any(name == package or name.startswith(package + ".") for package in blocked)
)
if loaded:
    raise SystemExit("Optional engine runtimes imported during startup: " + ", ".join(loaded))
"""
    result = subprocess.run(
        [sys.executable, "-c", check],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
