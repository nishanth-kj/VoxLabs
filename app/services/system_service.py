"""SystemService: health information and the small JSON settings file."""

import json
import platform
import sys
import threading

from app.constants.audio import DEFAULT_SAMPLE_RATE, EMOTIONS, ENHANCE_PRESETS, STYLES
from app.constants.models import DEFAULT_CLONE_MODEL, DEFAULT_TTS_MODEL
from app.exceptions import ValidationError
from app.utils import device, ffmpeg
from app.utils.database import database_path
from app.utils.files import data_dir
from app.utils.logger import get_recent_logs, logger, set_level

VERSION = "3.0.0"

DEFAULT_SETTINGS = {
    "output_device": "",
    "input_device": "",
    "default_voices_id": None,
    "default_tts_model": DEFAULT_TTS_MODEL,
    "default_clone_model": DEFAULT_CLONE_MODEL,
    "allow_online_models": False,
    "export_format": "wav",
    "sample_rate": DEFAULT_SAMPLE_RATE,
    "output_dir": "",
    "device": "auto",
    "enhance_preset": "Voice Clean",
    "autosave": True,
    "api_enabled": False,
    "api_host": "127.0.0.1",
    "api_port": 8942,
    "api_token": "",
    "log_level": "INFO",
}


class SystemService:
    def __init__(self):
        self._lock = threading.Lock()
        self._cache: dict | None = None

    # ------------------------------------------------------------ settings

    def _path(self):
        return data_dir() / "settings.json"

    def get_settings(self) -> dict:
        with self._lock:
            if self._cache is None:
                stored = {}
                path = self._path()
                if path.exists():
                    try:
                        stored = json.loads(path.read_text(encoding="utf-8"))
                    except (OSError, json.JSONDecodeError):
                        logger.warning("settings.json is unreadable; using defaults")
                self._cache = {**DEFAULT_SETTINGS, **{k: v for k, v in stored.items() if k in DEFAULT_SETTINGS}}
            return dict(self._cache)

    def get_setting(self, key: str):
        return self.get_settings().get(key, DEFAULT_SETTINGS.get(key))

    def update_settings(self, **changes) -> dict:
        unknown = set(changes) - set(DEFAULT_SETTINGS)
        if unknown:
            raise ValidationError(f"Unknown settings: {', '.join(sorted(unknown))}")
        if "api_port" in changes and not 1 <= int(changes["api_port"]) <= 65535:
            raise ValidationError("API port must be between 1 and 65535", field="api_port")
        settings = {**self.get_settings(), **changes}
        with self._lock:
            self._path().write_text(json.dumps(settings, indent=2), encoding="utf-8")
            self._cache = settings
        if "log_level" in changes:
            set_level(settings["log_level"])
        logger.info(f"Settings updated: {', '.join(sorted(changes))}")
        return dict(settings)

    def reset_cache(self) -> None:
        with self._lock:
            self._cache = None

    # ------------------------------------------------------------ startup

    def initialize(self) -> None:
        """Prepare data folders, the database and the model catalog. Safe to call repeatedly."""
        from app.services.job_service import job_service
        from app.services.model_service import model_service
        from app.utils.database import init_db
        from app.utils.files import ensure_data_dirs

        ensure_data_dirs()
        set_level(self.get_setting("log_level"))
        init_db()
        model_service.sync_catalog()
        interrupted = job_service.recover_interrupted()
        if interrupted:
            logger.info(f"Marked {interrupted} interrupted job(s) as failed")
        logger.info(f"VoxLabs {VERSION} ready (data: {data_dir()})")

    # ------------------------------------------------------------ optional REST API (desktop-hosted)

    _api_server = None
    _api_thread: threading.Thread | None = None

    def api_running(self) -> bool:
        return self._api_thread is not None and self._api_thread.is_alive()

    def start_api(self) -> None:
        """Serve the REST API from inside the desktop app on a background thread."""
        import uvicorn

        from app.api.app import create_app

        if self.api_running():
            return
        settings = self.get_settings()
        host = settings["api_host"] or "127.0.0.1"
        if host not in ("127.0.0.1", "localhost", "::1") and not settings["api_token"]:
            raise ValidationError("Set an API token before exposing the API beyond this computer",
                                  field="api_token")
        config = uvicorn.Config(create_app(initialize=False), host=host, port=int(settings["api_port"]),
                                log_level="warning")
        self._api_server = uvicorn.Server(config)
        self._api_thread = threading.Thread(target=self._api_server.run, name="voxlabs-api", daemon=True)
        self._api_thread.start()
        logger.info(f"REST API started on http://{host}:{settings['api_port']}")

    def stop_api(self) -> None:
        if self._api_server is not None:
            self._api_server.should_exit = True
            if self._api_thread:
                self._api_thread.join(timeout=5)
            logger.info("REST API stopped")
        self._api_server = self._api_thread = None

    def apply_api_setting(self) -> None:
        """Start, restart or stop the embedded API to match the current settings."""
        self.stop_api()
        if self.get_setting("api_enabled"):
            self.start_api()

    # ------------------------------------------------------------ info

    def health(self) -> dict:
        return {
            "status": "ok",
            "version": VERSION,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "ffmpeg": ffmpeg.version(),
            "database": str(database_path()),
            "data_dir": str(data_dir()),
        }

    def devices(self) -> dict:
        return device.summary()

    def presets(self) -> dict:
        return {"emotions": EMOTIONS, "styles": list(STYLES), "enhance_presets": ENHANCE_PRESETS}

    def logs(self, limit: int = 200) -> list[dict]:
        return get_recent_logs(max(1, min(limit, 500)))


system_service = SystemService()
