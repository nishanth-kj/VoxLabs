"""Desktop pages. `BasePage` gives every page the same helpers for background work."""

from collections.abc import Callable

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.ui.widgets.progress import BusyBar, run_async, show_error, watch_job


class BasePage(QWidget):
    title = ""

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.state = state
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(18, 14, 18, 14)
        heading = QLabel(self.title)
        heading.setObjectName("PageTitle")
        self.root.addWidget(heading)
        self.busy = BusyBar()
        self.root.addWidget(self.busy)

    # Called by MainWindow whenever the page becomes visible.
    def refresh(self) -> None:
        pass

    def error(self, exc) -> None:
        self.busy.stop()
        show_error(self, exc)

    def run(self, fn: Callable, on_done: Callable | None = None, busy: bool = True) -> None:
        """Run a quick service call off the UI thread."""
        if busy:
            self.busy.start(indeterminate=True)

        def done(result):
            self.busy.stop()
            if on_done:
                on_done(result)

        run_async(fn, done, self.error, parent=self)

    def follow(self, job: dict, on_done: Callable[[dict], None] | None = None,
               on_fail: Callable[[], None] | None = None) -> None:
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
