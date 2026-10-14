"""SystemService: health information and the small JSON settings file."""

import json
import os
import platform
import sys
import threading

from app.constants.audio import DEFAULT_SAMPLE_RATE, EMOTIONS, ENHANCE_PRESETS, STYLES
from app.constants.models import DEFAULT_CLONE_MODEL, DEFAULT_TTS_MODEL
from app.constants.performance import (
    BATCH_SIZE_MAX,
    DEFAULT_PERFORMANCE_PRESET,
    JOB_WORKERS_MAX,
    PERFORMANCE_PRESETS,
    PRECISIONS,
)
from app.exceptions import ValidationError, service_error
from app.models.request.performance_request import PerformanceRequest
from app.utils import device, ffmpeg
from app.utils.database import database_path
from app.utils.files import data_dir
from app.utils.logger import LOG_BUFFER_SIZE, get_recent_logs, logger, set_level

from app.constants.version import VERSION

DEFAULT_SETTINGS = {
    "output_device": "",
    "input_device": "",
    "default_voices_id": None,
    "builtin_voices_seeded": False,  # set by builds before `builtin_voice_packs`; read only
    "builtin_voice_packs": [],
    "default_tts_model": DEFAULT_TTS_MODEL,
    "default_clone_model": DEFAULT_CLONE_MODEL,
    "allow_online_models": False,
    "allow_edge": False,
    "export_format": "wav",
    "sample_rate": DEFAULT_SAMPLE_RATE,
    "output_dir": "",
    "device": "auto",
    "enhance_preset": "Voice Clean",
    "autosave": True,
    "pronunciations": {},
    "api_enabled": False,
    "api_host": "127.0.0.1",
    "api_port": 8942,
    "api_token": "",
    "log_level": "INFO",
    "theme": "system",
    "native_title_bar": False,
    "sidebar_collapsed": False,
    # Performance (app/constants/performance.py): a preset fills in the values after it.
    "performance_preset": DEFAULT_PERFORMANCE_PRESET,
    **PERFORMANCE_PRESETS[DEFAULT_PERFORMANCE_PRESET],
}
# Integer performance settings and their allowed range.
_RANGES = {"max_loaded_models": (0, 16), "gpu_memory_budget_mb": (0, 1 << 20), "gpu_memory_reserve_mb": (0, 1 << 16),
           "batch_size": (1, BATCH_SIZE_MAX), "job_workers": (1, JOB_WORKERS_MAX)}


class SystemService:
    def __init__(self):
        self._lock = threading.Lock()
        self._cache: dict | None = None

    # ------------------------------------------------------------ settings

    def _path(self):
        return data_dir() / "settings.json"

    def get_settings(self) -> dict:
        try:
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
        except Exception as exc:
            raise service_error(exc, "system_service.get_settings")

    def get_setting(self, key: str):
        try:
            return self.get_settings().get(key, DEFAULT_SETTINGS.get(key))
        except Exception as exc:
            raise service_error(exc, "system_service.get_setting")

    def update_settings(self, **changes) -> dict:
        try:
            unknown = set(changes) - set(DEFAULT_SETTINGS)
            if unknown:
                raise ValidationError(f"Unknown settings: {', '.join(sorted(unknown))}")
            if "api_port" in changes and not 1 <= int(changes["api_port"]) <= 65535:
                raise ValidationError("API port must be between 1 and 65535", field="api_port")
            for key, (low, high) in _RANGES.items():
                if key in changes and not low <= int(changes[key]) <= high:
                    raise ValidationError(f"{key} must be between {low} and {high}", field=key)
            if "precision" in changes and changes["precision"] not in PRECISIONS:
                raise ValidationError(f"precision must be one of: {', '.join(PRECISIONS)}", field="precision")
            if "performance_preset" in changes and changes["performance_preset"] not in (*PERFORMANCE_PRESETS, "custom"):
                raise ValidationError(f"Unknown performance preset '{changes['performance_preset']}'",
                                      field="performance_preset")
            settings = {**self.get_settings(), **changes}
            with self._lock:
                self._path().write_text(json.dumps(settings, indent=2), encoding="utf-8")
                self._cache = settings
            if "log_level" in changes:
                set_level(settings["log_level"])
            logger.info(f"Settings updated: {', '.join(sorted(changes))}")
            return dict(settings)
        except Exception as exc:
            raise service_error(exc, "system_service.update_settings")

    def apply_performance_preset(self, preset: str) -> dict:
        """Copy a preset's values into the individual performance settings."""
        try:
            if preset not in PERFORMANCE_PRESETS:
                raise ValidationError(f"Unknown performance preset '{preset}'", field="performance_preset")
            return self.update_settings(performance_preset=preset, **PERFORMANCE_PRESETS[preset])
        except Exception as exc:
            raise service_error(exc, "system_service.apply_performance_preset")

    def performance(self) -> dict:
        """The performance settings, the presets, this computer's hardware and the preset recommended for it."""
        try:
            settings = self.get_settings()
            return {"preset": settings["performance_preset"],
                    "settings": {key: settings[key] for key in PERFORMANCE_PRESETS[DEFAULT_PERFORMANCE_PRESET]},
                    "presets": PERFORMANCE_PRESETS, "hardware": device.summary()}
        except Exception as exc:
            raise service_error(exc, "system_service.performance")

    def save_performance(self, body: PerformanceRequest) -> dict:
        """Apply `body.preset`, then the values given; the preset becomes Custom unless they match one exactly.
        Loaded models are unloaded when the precision changes, so they load again with it."""
        try:
            before = self.get_setting("precision")
            if body.preset:
                self.apply_performance_preset(body.preset)
            changes = body.model_dump(exclude_unset=True, exclude_none=True, exclude={"preset"})
            if changes:
                values = {**{key: self.get_setting(key) for key in PERFORMANCE_PRESETS[DEFAULT_PERFORMANCE_PRESET]},
                          **changes}
                preset = next((name for name, preset in PERFORMANCE_PRESETS.items() if preset == values), "custom")
                self.update_settings(performance_preset=preset, **changes)
            if self.get_setting("precision") != before:
                from app.services.model_service import model_service

                model_service.unload_all()
            return self.performance()
        except Exception as exc:
            raise service_error(exc, "system_service.save_performance")

    def reset_cache(self) -> None:
        try:
            with self._lock:
                self._cache = None
        except Exception as exc:
            raise service_error(exc, "system_service.reset_cache")

    # ------------------------------------------------------------ startup

    def initialize(self) -> None:
        """Prepare data folders, the database and the model catalog. Safe to call repeatedly."""
        from app.services.job_service import job_service
        from app.services.model_service import model_service
        from app.utils.database import init_db
        from app.utils.files import ensure_data_dirs

        try:
            ensure_data_dirs()
            set_level(self.get_setting("log_level") or "INFO")
            init_db()
            model_service.sync_catalog()
            interrupted = job_service.recover_interrupted()
            if interrupted:
                logger.info(f"Marked {interrupted} interrupted job(s) as failed")
            from app.services.voice_service import voice_service

            voice_service.ensure_builtin_voices()
            logger.info(f"VoxLabs {VERSION} ready (data: {data_dir()})")
        except Exception as exc:
            raise service_error(exc, "system_service.initialize")

    # ------------------------------------------------------------ optional REST API (desktop-hosted)

    _api_server = None
    _api_thread: threading.Thread | None = None

    def api_running(self) -> bool:
        try:
            return self._api_thread is not None and self._api_thread.is_alive()
        except Exception as exc:
            raise service_error(exc, "system_service.api_running")

    def check_api_host(self, host: str) -> None:
        """The API may leave this computer only behind a token (VOXLABS_API_TOKEN or Settings > API token)."""
        try:
            if host not in ("127.0.0.1", "localhost", "::1")                     and not (os.getenv("VOXLABS_API_TOKEN") or self.get_setting("api_token")):
                raise ValidationError("Set an API token before exposing the API beyond this computer",
                                      field="api_token")
        except Exception as exc:
            raise service_error(exc, "system_service.check_api_host")

    def start_api(self) -> None:
        """Serve the REST API from inside the desktop app on a background thread."""
        import uvicorn

        from app.api.app import create_app

        try:
            if self.api_running():
                return
            settings = self.get_settings()
            host = settings["api_host"] or "127.0.0.1"
            self.check_api_host(host)
            config = uvicorn.Config(create_app(initialize=False), host=host, port=int(settings["api_port"]),
                                    log_level="warning")
            self._api_server = uvicorn.Server(config)
            self._api_thread = threading.Thread(target=self._api_server.run, name="voxlabs-api", daemon=True)
            self._api_thread.start()
            logger.info(f"REST API started on http://{host}:{settings['api_port']}")
        except Exception as exc:
            raise service_error(exc, "system_service.start_api")

    def stop_api(self) -> None:
        try:
            if self._api_server is not None:
                self._api_server.should_exit = True
                if self._api_thread:
                    self._api_thread.join(timeout=5)
                logger.info("REST API stopped")
            self._api_server = self._api_thread = None
        except Exception as exc:
            raise service_error(exc, "system_service.stop_api")

    def apply_api_setting(self) -> None:
        """Start, restart or stop the embedded API to match the current settings."""
        try:
            self.stop_api()
            if self.get_setting("api_enabled"):
                self.start_api()
        except Exception as exc:
            raise service_error(exc, "system_service.apply_api_setting")

    # ------------------------------------------------------------ info

    def health(self) -> dict:
        try:
            return {
                "status": "ok",
                "version": VERSION,
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "ffmpeg": ffmpeg.version(),
                "database": str(database_path()),
                "data_dir": str(data_dir()),
            }
        except Exception as exc:
            raise service_error(exc, "system_service.health")

    def devices(self) -> dict:
        try:
            return device.summary()
        except Exception as exc:
            raise service_error(exc, "system_service.devices")

    def presets(self) -> dict:
        try:
            return {"emotions": EMOTIONS, "styles": list(STYLES), "enhance_presets": ENHANCE_PRESETS}
        except Exception as exc:
            raise service_error(exc, "system_service.presets")

    def logs(self, limit: int = 200, after: int = 0) -> list[dict]:
        """Recent log records (newest last); `after` returns only records with a larger `seq`."""
        try:
            return get_recent_logs(max(1, min(limit, LOG_BUFFER_SIZE)), after)
        except Exception as exc:
            raise service_error(exc, "system_service.logs")


system_service = SystemService()
