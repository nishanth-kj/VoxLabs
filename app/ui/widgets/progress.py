"""Keeping the UI responsive: run work off the Qt thread and follow background jobs.

- `run_async(fn, on_done, on_error)` runs a short call on QThreadPool (no job record).
- `JobBridge` relays JobService listener callbacks (worker threads) into Qt signals.
- `watch_job(job, on_done, on_error, on_progress)` calls back when a job finishes.
"""

import traceback
from collections.abc import Callable

import shiboken6
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot
from PySide6.QtWidgets import QMessageBox, QProgressBar, QWidget

from app.exceptions import AppError
from app.services.job_service import job_service
from app.utils.logger import logger


def error_message(exc: BaseException | str) -> str:
    """User-facing text for an exception (no stack traces)."""
    if isinstance(exc, str):
        return exc
    if isinstance(exc, AppError):
        return exc.message
    return f"Something went wrong: {exc}"


def show_error(parent: QWidget | None, exc: BaseException | str, title: str = "VoxLabs") -> None:
    message = error_message(exc)
    logger.warning(f"{title}: {message}")
    QMessageBox.warning(parent, title, message)


class _Relay(QObject):
    """Lives on the UI thread. Signals emitted from a worker reach its slots via a
    queued connection, so the callbacks always run on the UI thread."""

    done = Signal(object)
    failed = Signal(object)

    def __init__(self, on_done: Callable | None, on_error: Callable | None, parent: QWidget | None):
        super().__init__()
        self._on_done, self._on_error, self._parent = on_done, on_error, parent
        self.done.connect(self._handle_done)
        self.failed.connect(self._handle_failed)

    def _parent_gone(self) -> bool:
        # The page may have been closed while the work was running.
        return self._parent is not None and not shiboken6.isValid(self._parent)

    @Slot(object)
    def _handle_done(self, value):
        _live.discard(self)
        if self._on_done and not self._parent_gone():
            self._on_done(value)

    @Slot(object)
    def _handle_failed(self, exc):
        _live.discard(self)
        if self._parent_gone():
            return
        if self._on_error:
            self._on_error(exc)
        else:
            show_error(self._parent, exc)


class _Task(QRunnable):
    def __init__(self, fn: Callable, relay: _Relay):
        super().__init__()
        self.fn = fn
        self.relay = relay

    def run(self):
        try:
            result = self.fn()
        except Exception as exc:  # delivered to the UI thread as a message
            if not isinstance(exc, AppError):
                logger.error("Background task failed:\n" + traceback.format_exc())
            self.relay.failed.emit(exc)
        else:
            self.relay.done.emit(result)


_live: set[_Relay] = set()


def run_async(fn: Callable, on_done: Callable | None = None, on_error: Callable | None = None,
              parent: QWidget | None = None) -> None:
    """Run `fn()` on the thread pool; callbacks run on the UI thread."""
    relay = _Relay(on_done, on_error, parent)
    _live.add(relay)  # keep the relay alive until it has delivered
    QThreadPool.globalInstance().start(_Task(fn, relay))


class JobBridge(QObject):
    """Singleton that turns JobService notifications (from worker threads) into a UI-thread signal."""

    job_changed = Signal(dict)
    _incoming = Signal(dict)
    _instance: "JobBridge | None" = None

    def __init__(self):
        super().__init__()
        # Emitted from worker threads; the bound slot makes the connection queued.
        self._incoming.connect(self._deliver)

    @Slot(dict)
    def _deliver(self, job: dict):
        self.job_changed.emit(job)

    @classmethod
    def instance(cls) -> "JobBridge":
        if cls._instance is None:
            cls._instance = cls()
            job_service.add_listener(cls._instance._incoming.emit)
        return cls._instance

    @classmethod
    def detach(cls) -> None:
        if cls._instance is not None:
            job_service.remove_listener(cls._instance._incoming.emit)
            cls._instance = None


def watch_job(job: dict, on_done: Callable[[dict], None] | None = None,
              on_error: Callable[[str], None] | None = None,
              on_progress: Callable[[float], None] | None = None,
              parent: QWidget | None = None) -> None:
    """Follow one job until it finishes; `on_done` receives the job's result dict."""
    bridge = JobBridge.instance()
    jobs_id = job["jobs_id"]
    state = {"finished": False}

    def handle(update: dict):
        if update["jobs_id"] != jobs_id or state["finished"]:
            return
        if parent is not None and not shiboken6.isValid(parent):
            state["finished"] = True
            bridge.job_changed.disconnect(handle)
            return
        if on_progress:
            on_progress(update["progress"])
        if not update["finished"]:
            return
        state["finished"] = True
        bridge.job_changed.disconnect(handle)
        if update["status_label"] == "Completed":
            if on_done:
                on_done(update["result"] or {})
        elif update["status_label"] == "Failed":
            (on_error or (lambda msg: show_error(parent, msg)))(update["error"] or "Job failed")
        elif on_error:
            on_error("Cancelled")

    bridge.job_changed.connect(handle)
    # The job may have finished before we connected.
    current = job_service.get(jobs_id)
    if current["finished"]:
        handle(current)


class BusyBar(QProgressBar):
    """Thin progress bar that shows while a page is working."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMaximumHeight(6)
        self.setTextVisible(False)
        self.setRange(0, 1000)
        self.hide()

    def start(self, indeterminate: bool = False):
        self.setRange(0, 0 if indeterminate else 1000)
        self.setValue(0)
        self.show()

    def set_progress(self, value: float):
        self.setRange(0, 1000)
        self.setValue(int(value * 1000))

    def stop(self):
        self.hide()
