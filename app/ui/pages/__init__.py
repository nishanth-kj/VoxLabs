"""Desktop pages. `BasePage` gives every page the same header and helpers for background work."""

from collections.abc import Callable
from typing import Any

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

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

        def done(result):
            self.busy.stop()
            if on_done:
                on_done(result)

        def failed(message):
            self.busy.stop()
            if on_fail:
                on_fail()
            if message != "Cancelled":
                show_error(self, message)

        watch_job(job, done, failed, self.busy.set_progress, parent=self)
