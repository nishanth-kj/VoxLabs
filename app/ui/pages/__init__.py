"""Desktop pages. `BasePage` gives every page the same header and helpers for background work."""

from collections.abc import Callable
from typing import Any

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.services.tts_service import tts_service
from app.ui.widgets.progress import BusyBar, run_async, show_error, watch_job


class BasePage(QWidget):
    title = ""
    subtitle = ""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(24, 18, 24, 14)
        self.root.setSpacing(10)
        header = QVBoxLayout()
        header.setSpacing(2)
        heading = QLabel(self.title)
        heading.setObjectName("PageTitle")
        header.addWidget(heading)
        if self.subtitle:
            subtitle = QLabel(self.subtitle)
            subtitle.setObjectName("PageSubtitle")
            subtitle.setWordWrap(True)
            header.addWidget(subtitle)
        self.root.addLayout(header)
        self.busy = BusyBar()
        self.root.addWidget(self.busy)
        # What the followed job is doing, then how long it took (measured, never estimated up front).
        self.job_status = QLabel("")
        self.job_status.setObjectName("Hint")
        self.job_status.setWordWrap(True)
        self.job_status.hide()
        self.root.addWidget(self.job_status)

    # Called by MainWindow whenever the page becomes visible.
    def refresh(self) -> None:
        pass

    # Called by MainWindow after the theme changes, for pages that show icons.
    def refresh_icons(self) -> None:
        pass

    def error(self, exc) -> None:
        self.busy.stop()
        show_error(self, exc)

    def run(self, fn: Callable[[], Any], on_done: Callable[[Any], object] | None = None, busy: bool = True,
            on_error: Callable[[], object] | None = None) -> None:
        """Run a quick service call off the UI thread."""
        if busy:
            self.busy.start(indeterminate=True)

        def done(result):
            self.busy.stop()
            if on_done:
                on_done(result)

        def failed(exc):
            self.error(exc)
            if on_error:
                on_error()

        run_async(fn, done, failed, parent=self)

    def follow(self, job: dict, on_done: Callable[[dict], object] | None = None,
               on_fail: Callable[[], object] | None = None) -> None:
        """Show progress for a background job and call `on_done(result)` when it completes."""
        self.busy.start()
        self.job_status.hide()

        def done(result):
            self.busy.stop()
            self._show_timings(result.get("timings"))
            if on_done:
                on_done(result)

        def failed(message):
            self.busy.stop()
            self.job_status.hide()
            if on_fail:
                on_fail()
            if message != "Cancelled":
                show_error(self, message)

        def says(message: str):
            self.job_status.setText(message)
            self.job_status.show()

        watch_job(job, done, failed, self.busy.set_progress, parent=self, on_message=says)

    def _show_timings(self, timings: dict | None) -> None:
        """After a generation: audio length, time taken, RTF and where the time went (queue, load, ...)."""
        text = tts_service.describe(timings) if timings and timings.get("audio_s") else ""
        self.job_status.setText(text)
        self.job_status.setVisible(bool(text))
