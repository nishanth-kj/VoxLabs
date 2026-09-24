"""Status-bar job indicator and the jobs panel (progress, status, error, times, cancel)."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.job_service import job_service
from app.ui.widgets.progress import JobBridge, run_async, show_error
from app.utils.time import local_display


class JobsDialog(QDialog):
    COLUMNS = ("Job", "Status", "Progress", "Error", "Started", "Finished")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Background jobs")
        self.resize(820, 380)
        self.table = QTableWidget(0, len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        cancel = QPushButton("Cancel selected job")
        cancel.clicked.connect(self.cancel_selected)
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        buttons = QHBoxLayout()
        buttons.addWidget(refresh)
        buttons.addStretch()
        buttons.addWidget(cancel)
        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addLayout(buttons)
        JobBridge.instance().job_changed.connect(lambda _job: self.refresh())
        self.refresh()

    def refresh(self):
        jobs = job_service.list_jobs(limit=100)
        self.table.setRowCount(len(jobs))
        for row, job in enumerate(jobs):
            values = (job["title"], job["status_label"], f"{job['progress'] * 100:.0f}%", job["error"] or "",
                      local_display_iso(job["started_at"]), local_display_iso(job["finished_at"]))
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, job["jobs_id"])
                self.table.setItem(row, col, item)

    def cancel_selected(self):
        item = self.table.currentItem()
        if item is None:
            return
        run_async(lambda: job_service.cancel(item.data(Qt.UserRole)), lambda _r: self.refresh(),
                  lambda exc: show_error(self, exc))


def local_display_iso(value: str | None) -> str:
    if not value:
        return ""
    from datetime import datetime

    return local_display(datetime.fromisoformat(value))


class JobStatusWidget(QWidget):
    """Compact indicator: "2 jobs running" plus the progress of the newest active job."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel("No active jobs")
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setMaximumWidth(160)
        self.bar.setMaximumHeight(14)
        self.bar.setTextVisible(False)
        self.bar.hide()
        button = QPushButton("Jobs")
        button.setFlat(True)
        button.clicked.connect(self.open_dialog)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        layout.addWidget(self.bar)
        layout.addWidget(button)
        self._dialog: JobsDialog | None = None
        JobBridge.instance().job_changed.connect(self.on_job)
        self.on_job(None)

    def on_job(self, job):
        active = job_service.list_jobs(active_only=True)
        if not active:
            self.label.setText("No active jobs" if not job or job.get("status_label") != "Failed"
                               else f"Failed: {job['title']}")
            self.bar.hide()
            return
        newest = active[0]
        self.label.setText(f"{len(active)} job{'s' if len(active) > 1 else ''}: {newest['title']}")
        self.bar.setValue(int(newest["progress"] * 100))
        self.bar.show()

    def open_dialog(self):
        if self._dialog is None:
            self._dialog = JobsDialog(self.window())
        self._dialog.refresh()
        self._dialog.show()
        self._dialog.raise_()
