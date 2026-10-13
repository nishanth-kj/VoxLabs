"""ModelService: discover, install, load and select local AI models.

The `models` table mirrors the built-in catalog (plus Piper voices the user
drops into data/models). Loaded backends are kept in memory here — there is no
separate model-manager layer.

Lifecycle: a model is loaded once and reused by every generation (`using()`).
Loads run one at a time, so free memory is checked and then filled without a race,
but a load never blocks generations on models that are already loaded. When a model
does not fit on the GPU, idle models there are unloaded, least recently used first;
`max_loaded_models` caps how many stay in memory at all.
"""

import json
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import select

from app.constants.jobs import JobType
from app.constants.models import (
    CLONING_BACKENDS,
    DEFAULT_TTS_MODEL,
    ENGINE_INSTALL_COMMAND,
    FALLBACK_TTS_MODELS,
    FETCH_ON_LOAD_BACKENDS,
    MODEL_CATALOG,
    Backend,
    ModelType,
)
from app.constants.status import Status
from app.exceptions import JobCancelled, ModelError, NotFoundError, ValidationError, service_error
from app.models import Model
from app.services.job_service import job_service
from app.services.system_service import system_service
from app.utils import device as device_utils
from app.utils.database import read_session, serialize, transaction
from app.utils.files import link_file, remove_tree, subdir
from app.utils.logger import logger
from app.utils.model import (
    ModelBackend,
    backend_class,
    create_backend,
    create_environment,
    download,
    environment_dir,
    environment_gpu_upgrade,
    environment_ready,
    environment_supported,
    is_cuda_oom,
    package_installed,
    release_memory,
)

_CATALOG = {entry["key"]: entry for entry in MODEL_CATALOG}
# Backends that are built into VoxLabs and never synthesize speech.
_NON_TTS = (Backend.MFCC, Backend.DSP)



def engine_hint(extra: str | None) -> str:
    """How to add a missing engine: a uv command when run from source; a built app cannot add one."""
    if getattr(sys, "frozen", False):
        return ("this copy of VoxLabs was built without it (rebuild with the engine installed: "
                + ENGINE_INSTALL_COMMAND.format(extra=extra) + ", then uv run build)")
    return "close VoxLabs and run: " + ENGINE_INSTALL_COMMAND.format(extra=extra)


class ModelService:
    def __init__(self):
        self._loaded: dict[str, ModelBackend] = {}
        self._last_used: dict[str, float] = {}
        self._lock = threading.RLock()  # guards _loaded and _last_used; never held while a model loads
        self._load_lock = threading.Lock()  # one load or unload at a time

    # ------------------------------------------------------------ catalog / discovery

    def model_dir(self, key: str) -> Path:
        return subdir("models") / key

    def _files_present(self, key: str, entry: dict | None) -> bool:
        files = (entry or {}).get("files")
        if not files:
            return True
        folder = self.model_dir(key)
        return all(self._weight_file(folder / name) for name in files)

    @staticmethod
    def _weight_file(path: Path) -> bool:
        return path.is_file() and path.stat().st_size > 0

    def is_installed(self, key: str, backend: str | None = None) -> bool:
        try:
            entry = _CATALOG.get(key)
            if entry is None:  # user-added Piper voice
                return backend == Backend.PIPER and (self.model_dir(key) / "model.onnx").exists() \
                    and package_installed("piper")
            return self._engine_ready(entry) and self._files_present(key, entry)
        except Exception as exc:
            raise service_error(exc, "model_service.is_installed")

    @staticmethod
    def _engine_ready(entry: dict | None) -> bool:
        """The engine's Python packages: a VoxLabs extra, or the model's own engine environment."""
        entry = entry or {}
        return package_installed(entry.get("package")) and environment_ready(entry.get("environment"))

    def sync_catalog(self) -> None:
        """Upsert catalog entries and scan data/models for user-added Piper voices."""
        try:
            with transaction() as session:
                rows = {m.key: m for m in session.scalars(select(Model))}
                for entry in MODEL_CATALOG:
                    row = rows.get(entry["key"])
                    if row is None:
                        row = Model(key=entry["key"])
                        session.add(row)
                    for field in ("name", "model_type", "backend", "version", "size_mb", "vram_mb", "capabilities",
                                  "online"):
                        setattr(row, field, entry[field])
                    self._refresh_row(row)
                for onnx in subdir("models").glob("*/model.onnx"):
                    key = onnx.parent.name
                    if key in _CATALOG:
                        continue
                    row = rows.get(key)
                    if row is None:
                        row = Model(key=key)
                        session.add(row)
                    row.name = self._piper_name(onnx) or key
                    row.model_type, row.backend, row.version = ModelType.TTS, Backend.PIPER, "custom"
                    row.size_mb = onnx.stat().st_size // (1 << 20)
                    row.capabilities, row.online = ["tts", "speed", "local"], False
                    self._refresh_row(row)
                # Retired engines (e.g. XTTS v2 and F5-TTS) leave rows behind: hide them.
                user_voices = {onnx.parent.name for onnx in subdir("models").glob("*/model.onnx")}
                for key, row in rows.items():
                    if key not in _CATALOG and key not in user_voices:
                        row.status = Status.DELETED.code
        except Exception as exc:
            raise service_error(exc, "model_service.sync_catalog")

    def _piper_name(self, onnx: Path) -> str | None:
        config = onnx.with_suffix(".onnx.json")
        try:
            data = json.loads(config.read_text(encoding="utf-8"))
            return f"Piper · {data.get('dataset') or onnx.parent.name} ({data.get('language', {}).get('code', '')})"
        except (OSError, json.JSONDecodeError):
            return None

    def _refresh_row(self, row: Model) -> None:
        installed = self.is_installed(row.key, row.backend)
        row.status = Status.ACTIVE.code if installed else Status.INACTIVE.code
        folder = self.model_dir(row.key)
        row.installed_path = str(folder) if installed else None

    def discover(self) -> list[dict]:
        try:
            self.sync_catalog()
            return self.list_models()
        except Exception as exc:
            raise service_error(exc, "model_service.discover")

    # ------------------------------------------------------------ read

    def to_dict(self, row: Model) -> dict:
        entry = _CATALOG.get(row.key, {})
        data = serialize(row)
        loaded = self._loaded.get(row.key)
        allow_online = bool(system_service.get_setting("allow_online_models"))
        data.update(
            installed=row.status == Status.ACTIVE.code,
            loaded=loaded is not None,
            loaded_device=loaded.device if loaded else None,
            package=entry.get("package"),
            package_installed=self._engine_ready(entry),
            extra=entry.get("extra"),
            environment=entry.get("environment"),
            needs_download=bool(entry.get("files")),
            files_ready=self._files_present(row.key, entry) if entry.get("files") else False,
            supports_cloning=row.backend in CLONING_BACKENDS,
            speaks=row.backend not in _NON_TTS,
            allowed=allow_online or not row.online,
            install_label=self._install_label(row, entry),
        )
        return data

    def _install_label(self, row: Model, entry: dict) -> str:
        """Why a model is or is not ready: shown on the Models and Home pages and in model pickers."""
        if row.status == Status.ACTIVE.code:
            if environment_gpu_upgrade(entry.get("environment")):
                return "Installed · CPU only (Install again to use the GPU)"
            return "Installed"
        if not self._files_present(row.key, entry):
            return "Not downloaded"
        if not environment_ready(entry.get("environment")):
            if not environment_supported():
                return "Downloaded · needs uv to set up its engine"
            return "Downloaded · engine not set up (Install sets it up)"
        if not package_installed(entry.get("package")):
            if getattr(sys, "frozen", False):
                return f"Downloaded · this app does not include the {entry.get('extra')} engine"
            return f"Downloaded · needs the {entry.get('extra')} engine"
        return "Not installed"

    def _row(self, session, model_ref: str | int) -> Model:
        if isinstance(model_ref, int) or str(model_ref).isdigit():
            row = session.get(Model, int(model_ref))
        else:
            row = session.scalar(select(Model).where(Model.key == str(model_ref)))
        if row is None:
            raise NotFoundError(f"Model '{model_ref}' not found", field="model")
        return row

    def get(self, model_ref: str | int) -> dict:
        try:
            with read_session() as session:
                return self.to_dict(self._row(session, model_ref))
        except Exception as exc:
            raise service_error(exc, "model_service.get")

    def list_models(self, model_type: str | None = None, speaking_only: bool = False) -> list[dict]:
        try:
            with read_session() as session:
                query = select(Model).where(Model.status != Status.DELETED.code)
                if model_type:
                    query = query.where(Model.model_type == model_type)
                models = [self.to_dict(m) for m in session.scalars(query.order_by(Model.online, Model.name))]
            return [m for m in models if m["speaks"]] if speaking_only else models
        except Exception as exc:
            raise service_error(exc, "model_service.list_models")

    # ------------------------------------------------------------ install / remove

    def install(self, model_ref: str | int, progress=None, cancelled=None) -> dict:
        try:
            model = self.get(model_ref)
            key = model["key"]
            entry = _CATALOG.get(key, {})
            files = entry.get("files") or {}
            for index, (name, url) in enumerate(files.items()):
                target = self.model_dir(key) / name
                if self._weight_file(target):
                    continue
                # The same file listed twice (e.g. a tokenizer two models share) is downloaded once.
                twin = next((self.model_dir(key) / other for other, other_url in files.items()
                             if other_url == url and other != name and self._weight_file(self.model_dir(key) / other)),
                            None)
                if twin is not None:
                    link_file(twin, target)
                    continue
                logger.info(f"Downloading {name} for {key}")
                download(url, target, cancelled=cancelled,
                         progress=(lambda v, i=index: progress((i + v) / len(files))) if progress else None)
            environment = entry.get("environment")
            if environment and not environment_ready(environment):
                create_environment(environment, cancelled=cancelled)
            elif environment_gpu_upgrade(environment):
                logger.info(f"Replacing the CPU-only PyTorch of the {environment} engine with a GPU build")
                self.unload(key)
                create_environment(environment, cancelled=cancelled, reinstall_torch=True)
            if not package_installed(entry.get("package")):
                extra = entry.get("extra")
                if files:
                    logger.info(f"Model {key} weights saved; Python extra '{extra}' is not installed")
                    with transaction() as session:
                        row = self._row(session, key)
                        self._refresh_row(row)
                        return self.to_dict(row)
                raise ModelError(f"{model['name']} needs its {extra} engine: {engine_hint(extra)}.")
            if model["backend"] in FETCH_ON_LOAD_BACKENDS:
                # These libraries fetch their weights on first load; do it now so the download is visible.
                self.load(key)
            with transaction() as session:
                row = self._row(session, key)
                self._refresh_row(row)
                logger.info(f"Model {key} installed")
                return self.to_dict(row)
        except Exception as exc:
            raise service_error(exc, "model_service.install")

    def install_async(self, model_ref: str | int) -> dict:
        try:
            model = self.get(model_ref)
            return job_service.submit(
                JobType.MODEL_INSTALL,
                lambda ctx: {"model": self.install(model["key"], progress=ctx.progress, cancelled=lambda: ctx.cancelled)},
                title=f"Install {model['name']}",
                params={"model": model["key"]},
            )
        except Exception as exc:
            raise service_error(exc, "model_service.install_async")

    def install_all(self, progress=None, cancelled=None) -> dict:
        """Download every local model that still needs weights. One failure does not stop the rest.

        Models with no direct files and no installed Python extra are skipped with the `uv sync`
        command, instead of failing the batch.
        """
        try:
            targets: list[dict] = []
            skipped: list[dict] = []
            for model in self.list_models():
                if model["online"] or not model["speaks"]:
                    continue
                entry = _CATALOG.get(model["key"], {})
                files = entry.get("files") or {}
                files_missing = bool(files) and not self._files_present(model["key"], entry)
                package_ok = package_installed(entry.get("package"))
                needs_library = model["backend"] in FETCH_ON_LOAD_BACKENDS and package_ok and not model["installed"]
                needs_environment = not environment_ready(entry.get("environment"))
                if needs_environment and not environment_supported():
                    skipped.append({"key": model["key"], "name": model["name"],
                                    "reason": "needs uv to set up its engine environment (https://docs.astral.sh/uv/)"})
                elif files_missing or needs_library or needs_environment:
                    targets.append(model)
                elif not package_ok and entry.get("extra") and not files:
                    # Weights that have a URL are downloaded above. This is only for engines
                    # whose library fetches its own files and is not installed yet.
                    skipped.append({"key": model["key"], "name": model["name"],
                                    "reason": engine_hint(entry["extra"])})
            downloaded: list[dict] = []
            failed: list[dict] = []
            count = len(targets)
            for index, model in enumerate(targets):
                if cancelled and cancelled():
                    raise JobCancelled("Download cancelled")
                if progress:
                    progress(index / count if count else 1)

                def scaled(value, i=index):
                    if progress:
                        progress((i + value) / count if count else 1)

                try:
                    saved = self.install(model["key"], progress=scaled, cancelled=cancelled)
                    downloaded.append({"key": model["key"], "name": model["name"],
                                       "ready": bool(saved.get("installed") or saved.get("files_ready"))})
                except JobCancelled:
                    raise
                except Exception as exc:
                    failed.append({"key": model["key"], "name": model["name"],
                                   "error": getattr(exc, "message", str(exc))})
            if progress:
                progress(1)
            logger.info(f"Downloaded {len(downloaded)} model(s), skipped {len(skipped)}, failed {len(failed)}")
            return {"downloaded": downloaded, "skipped": skipped, "failed": failed}
        except Exception as exc:
            raise service_error(exc, "model_service.install_all")

    def install_all_async(self) -> dict:
        try:
            return job_service.submit(
                JobType.MODEL_INSTALL,
                lambda ctx: self.install_all(progress=ctx.progress, cancelled=lambda: ctx.cancelled),
                title="Download all models",
            )
        except Exception as exc:
            raise service_error(exc, "model_service.install_all_async")

    def remove(self, model_ref: str | int) -> dict:
        try:
            model = self.get(model_ref)
            self.unload(model["key"])
            if model["size_mb"] or model["needs_download"]:
                remove_tree(self.model_dir(model["key"]))
            if model["environment"]:
                remove_tree(environment_dir(model["environment"]))
            with transaction() as session:
                row = self._row(session, model["key"])
                self._refresh_row(row)
                return self.to_dict(row)
        except Exception as exc:
            raise service_error(exc, "model_service.remove")

    # ------------------------------------------------------------ load / unload

    def pick_device(self, model: dict, requested: str | None = None) -> str:
        """Device policy: explicit request > settings > CUDA when the model fits in free VRAM > CPU.

        To fit a model on the GPU, idle models there are unloaded first (least recently used first).
        """
        try:
            requested = requested or system_service.get_setting("device") or "auto"
            if requested == "auto" and not model["vram_mb"]:
                return "cpu"  # a CPU model (Piper): no need to ask about GPUs
            cls = backend_class(model["backend"])
            available = cls.available_devices() if cls else device_utils.available_devices()
            if requested != "auto":
                if requested not in available:
                    raise ModelError(f"Device '{requested}' is not available (have: {', '.join(available)})")
                if requested.startswith("cuda") and model["vram_mb"]:
                    self._make_room(model, requested)
                return requested
            if model["vram_mb"] and len(available) > 1 and self._make_room(model, "cuda:0"):
                return "cuda:0"
            return "cpu"
        except Exception as exc:
            raise service_error(exc, "model_service.pick_device")

    def _fits(self, model: dict, device: str) -> bool:
        """The model's VRAM estimate fits in free VRAM (minus the reserve) and in the VRAM budget."""
        index = int(device.split(":")[1]) if ":" in device else 0
        gpu = next((g for g in device_utils.gpus() if g["index"] == index), None)
        if gpu is None:
            return False
        settings = system_service.get_settings()
        if gpu["vram_free_mb"] - int(settings["gpu_memory_reserve_mb"] or 0) < model["vram_mb"]:
            return False
        budget = int(settings["gpu_memory_budget_mb"] or 0)
        return not budget or self._gpu_mb_in_use() + model["vram_mb"] <= budget

    def _gpu_mb_in_use(self) -> int:
        with self._lock:
            return sum(_CATALOG.get(key, {}).get("vram_mb", 0) for key, backend in self._loaded.items()
                       if backend.device.startswith("cuda"))

    def _make_room(self, model: dict, device: str) -> bool:
        """Unload idle GPU models, least recently used first, until `model` fits. False when it still does not."""
        for victim in self._eviction_order(exclude=model["key"], gpu_only=True):
            if self._fits(model, device):
                return True
            if self._evict(victim):
                logger.info(f"Unloaded {victim} to make room on the GPU for {model['key']}")
        return self._fits(model, device)

    def _eviction_order(self, exclude: str, gpu_only: bool = False) -> list[str]:
        with self._lock:
            keys = [key for key, backend in self._loaded.items()
                    if key != exclude and (not gpu_only or backend.device.startswith("cuda"))]
            return sorted(keys, key=lambda key: self._last_used.get(key, 0.0))

    def _evict(self, key: str) -> bool:
        """Unload `key` unless a generation is using it right now."""
        with self._lock:
            backend = self._loaded.get(key)
        if backend is None or not backend.lock.acquire(blocking=False):
            return False
        try:
            with self._lock:
                if self._loaded.get(key) is backend:
                    del self._loaded[key]
                    self._last_used.pop(key, None)
            backend.unload()
        finally:
            backend.lock.release()
        release_memory(backend.device)
        return True

    def _respect_limit(self, key: str) -> None:
        """Make space under max_loaded_models before `key` loads (idle models only, oldest first)."""
        limit = int(system_service.get_setting("max_loaded_models") or 0)
        if not limit:
            return
        for victim in self._eviction_order(exclude=key):
            if len(self._loaded) < limit:
                return
            if self._evict(victim):
                logger.info(f"Unloaded {victim}: at most {limit} model(s) stay loaded")

    def load(self, model_ref: str | int, device: str | None = None, warm_up: bool = False) -> dict:
        """Load a model once (later calls reuse it). `warm_up` speaks a word right after loading, for loads that
        run ahead of a generation (Load, preload), so the first generation does not pay one-time costs."""
        try:
            model = self.get(model_ref)
            key = model["key"]
            if not model["speaks"]:
                return model  # built-in helpers need no loading
            if not model["allowed"]:
                raise ModelError(f"{model['name']} is an online service. Enable online models in Settings to use it.")
            if backend_class(model["backend"]) is None:
                raise ModelError(f"No backend available for {model['name']}")
            if key in self._loaded:
                self._touch(key)
                return model
            with self._load_lock:
                if key in self._loaded:  # loaded by another thread while this one waited
                    self._touch(key)
                    return self.get(key)
                self._respect_limit(key)
                precision = system_service.get_setting("precision") or "auto"
                started = time.perf_counter()
                backend = create_backend(model["backend"], self.model_dir(key), self.pick_device(model, device),
                                         precision)
                try:
                    backend.load()
                except Exception as exc:
                    self._discard(backend)
                    if not (backend.device.startswith("cuda") and is_cuda_oom(exc)):
                        raise
                    # The GPU is too full (e.g. a local LLM is running): retry on the CPU instead of failing.
                    logger.warning(f"Not enough GPU memory for {key}; loading it on the CPU instead")
                    backend = create_backend(model["backend"], self.model_dir(key), "cpu", precision)
                    backend.load()
                if warm_up:
                    with backend.lock:
                        backend.warm_up()
                with self._lock:
                    self._loaded[key] = backend
                    self._last_used[key] = time.perf_counter()
            logger.info(f"Model {key} loaded on {backend.device} in {time.perf_counter() - started:.1f}s"
                        + (" (warmed up)" if warm_up else ""))
            return self.get(key)
        except Exception as exc:
            raise service_error(exc, "model_service.load")

    def load_async(self, model_ref: str | int) -> dict:
        try:
            model = self.get(model_ref)
            return job_service.submit(JobType.MODEL_LOAD, lambda ctx: {"model": self.load(model["key"], warm_up=True)},
                                      title=f"Load {model['name']}", params={"model": model["key"]})
        except Exception as exc:
            raise service_error(exc, "model_service.load_async")

    def preload_default(self) -> dict | None:
        """Load the default speech model in the background when `preload_default_model` is on."""
        try:
            if not system_service.get_setting("preload_default_model"):
                return None
            try:
                model = self.resolve_speech_model()
            except ModelError as exc:
                logger.info(f"Not preloading a speech model: {exc.message}")
                return None
            if model["key"] in self._loaded:
                return None
            return self.load_async(model["key"])
        except Exception as exc:
            raise service_error(exc, "model_service.preload_default")

    def unload(self, model_ref: str | int) -> dict:
        try:
            model = self.get(model_ref)
            with self._load_lock:
                with self._lock:
                    backend = self._loaded.pop(model["key"], None)
                    self._last_used.pop(model["key"], None)
                if backend:
                    with backend.lock:  # lets a generation in progress finish its current chunk
                        backend.unload()
                    release_memory(backend.device)
                    logger.info(f"Model {model['key']} unloaded")
            return self.get(model["key"])
        except Exception as exc:
            raise service_error(exc, "model_service.unload")

    def reload(self, model_ref: str | int) -> dict:
        try:
            self.unload(model_ref)
            return self.load(model_ref)
        except Exception as exc:
            raise service_error(exc, "model_service.reload")

    def unload_all(self) -> None:
        try:
            for key in list(self._loaded):
                self.unload(key)
        except Exception as exc:
            raise service_error(exc, "model_service.unload_all")

    def release_cached_memory(self) -> None:
        """Hand cached GPU memory back to the system (after a job, with release_memory_after_job)."""
        try:
            release_memory()
        except Exception as exc:
            raise service_error(exc, "model_service.release_cached_memory")

    def loaded_models(self) -> list[dict]:
        """What is in memory now: key, device and seconds since last use (most recent first)."""
        try:
            now = time.perf_counter()
            with self._lock:
                rows = [{"key": key, "device": backend.device, "precision": backend.precision,
                         "idle_s": round(now - self._last_used.get(key, now), 1)} for key, backend in self._loaded.items()]
            return sorted(rows, key=lambda row: row["idle_s"])
        except Exception as exc:
            raise service_error(exc, "model_service.loaded_models")

    @staticmethod
    def _discard(backend: ModelBackend) -> None:
        """Free what a failed load left behind, without hiding why it failed."""
        try:
            backend.unload()
        except Exception as exc:
            logger.debug(f"Cleaning up after a failed load: {exc!r}")
        release_memory(backend.device)

    def _touch(self, key: str) -> None:
        with self._lock:
            if key in self._loaded:
                self._last_used[key] = time.perf_counter()

    def health(self, model_ref: str | int) -> dict:
        try:
            model = self.get(model_ref)
            problems = []
            if not model["package_installed"]:
                problems.append("Engine not set up: install the model on the Models page" if model["environment"]
                                else f"Engine missing: {engine_hint(model['extra'])}")
            if model["needs_download"] and not self._files_present(model["key"], _CATALOG.get(model["key"])):
                problems.append("Model files not downloaded")
            if not model["allowed"]:
                problems.append("Online models are disabled in Settings")
            return {"model": model["key"], "ok": not problems, "problems": problems, "loaded": model["loaded"],
                    "device": model["loaded_device"]}
        except Exception as exc:
            raise service_error(exc, "model_service.health")

    # ------------------------------------------------------------ selection

    def select(self, model_type: str, model_ref: str | int) -> dict:
        try:
            model = self.get(model_ref)
            if model_type == ModelType.CLONE:
                system_service.update_settings(default_clone_model=model["key"])
            elif model_type == ModelType.TTS:
                if not model["speaks"]:
                    raise ValidationError(f"{model['name']} cannot generate speech")
                system_service.update_settings(default_tts_model=model["key"])
            else:
                raise ValidationError(f"Cannot select a default {model_type} model")
            return model
        except Exception as exc:
            raise service_error(exc, "model_service.select")

    def resolve_speech_model(self, model_ref: str | None = None, voice: dict | None = None) -> dict:
        """Pick the model for a generation.

        A voice is bound to its model. When that model speaks, it is used even if the request
        names a different one. A voice profile that cannot speak falls through to the requested
        model, then the default, then the first installed fallback.
        """
        try:
            bound = self.get(voice["model_key"]) if voice and voice.get("model_key") else None
            if bound is not None and bound["status"] == Status.DELETED.code:
                bound = None  # the voice's engine was retired: use the requested or default model
            if bound is not None and bound["speaks"]:
                model = bound
            elif model_ref:
                model = self.get(model_ref)
            else:
                model = self.get(system_service.get_setting("default_tts_model") or DEFAULT_TTS_MODEL)
                if not model["installed"]:
                    model = next((m for m in map(self._catalog_model, FALLBACK_TTS_MODELS)
                                  if m and m["installed"] and m["allowed"]), model)
            if not model["speaks"]:
                raise ModelError(f"{model['name']} cannot generate speech")
            if not model["installed"]:
                if not model["package_installed"] and model["environment"]:
                    raise ModelError(f"{model['name']} is not set up yet. Install it on the Models page.")
                if not model["package_installed"]:
                    raise ModelError(f"{model['name']} needs its {model['extra']} engine: "
                                     f"{engine_hint(model['extra'])}.")
                raise ModelError(f"{model['name']} is not downloaded yet. Download it on the Models page.")
            if not model["allowed"]:
                raise ModelError(f"{model['name']} is an online service. Enable online models in Settings to use it.")
            return model
        except Exception as exc:
            raise service_error(exc, "model_service.resolve_speech_model")

    def _catalog_model(self, key: str) -> dict | None:
        try:
            return self.get(key)
        except NotFoundError:
            return None

    def backend_for(self, model_ref: str) -> ModelBackend:
        """Return a loaded backend, loading it on first use."""
        try:
            backend = self._loaded.get(str(model_ref))
            if backend is not None:
                self._touch(str(model_ref))
                return backend
            key = self.get(model_ref)["key"]
            for _attempt in range(3):  # another job may unload it right after it loads (max_loaded_models)
                self.load(key)
                backend = self._loaded.get(key)
                if backend is not None:
                    return backend
            raise ModelError(f"Model {key} could not stay loaded. Try again, or raise the loaded-model limit.")
        except Exception as exc:
            raise service_error(exc, "model_service.backend_for")

    @contextmanager
    def using(self, model_ref: str) -> Iterator[ModelBackend]:
        """A loaded backend, held for one engine call so it is not unloaded underneath it.

        Only one call runs on a backend at a time (GPU memory and these models are not thread-safe); other
        jobs on the same model wait their turn between chunks. A model unloaded meanwhile is loaded again.
        """
        try:
            backend = self._acquire(model_ref)
        except Exception as exc:
            raise service_error(exc, "model_service.using")
        try:
            yield backend
        finally:
            backend.lock.release()

    def _acquire(self, model_ref: str) -> ModelBackend:
        for _attempt in range(3):
            backend = self.backend_for(model_ref)
            backend.lock.acquire()
            with self._lock:
                current = any(loaded is backend for loaded in self._loaded.values())
            if current and backend.loaded:
                return backend
            backend.lock.release()  # unloaded while this thread waited: load it again
        raise ModelError("The model was unloaded while it was in use. Try again.")


model_service = ModelService()
