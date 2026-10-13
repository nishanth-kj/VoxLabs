"""Files: everything VoxLabs keeps in one list — generated, imported, processed and rendered audio, exported
files and voice samples — with play, open in the editor, show in folder and delete."""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from app.constants.library import LIBRARY_KINDS
from app.constants.status import Status
from app.models.request import ExportRequest
from app.services.audio_service import audio_service
from app.ui.pages import BasePage
from app.ui.widgets.audio_player import AudioPlayer
from app.ui.widgets.select import Select
from app.utils.files import data_dir
from app.utils.time import format_duration, local_display

COLUMNS = ("Name", "Kind", "Format", "Length", "Size", "Created", "Folder", "File")


class FilesPage(BasePage):
    title = "Files"
    subtitle = ("Everything VoxLabs keeps: generated, imported, processed and edited audio, exported files and "
                "voice samples. Play one, open it in the editor, show it in its folder or delete it.")

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.items: list[dict] = []
        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name, format or folder")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _text: self._show(self.items))
        self.kind = Select()
        self.kind.addItem("Everything", None)
        for key, label in LIBRARY_KINDS.items():
            self.kind.addItem(label, key)
        self.kind.currentIndexChanged.connect(lambda _i: self._show(self.items))
        self.summary = QLabel("")
        self.summary.setObjectName("Hint")
        filters.addWidget(self.search, 1)
        filters.addWidget(self.kind)
        filters.addWidget(self.summary)
        self.root.addLayout(filters)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(lambda _item: self.play())
        self.root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        for label, slot in (("Play", self.play), ("Open in editor", self.open_in_editor),
                            ("Show in folder", self.show_in_folder), ("Copy path", self.copy_path),
                            ("Delete", self.delete)):
            button = QPushButton(label)
            button.clicked.connect(slot)
            actions.addWidget(button)
        actions.addStretch()
        folder = QPushButton("Open data folder")
        folder.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir()))))
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh)
        actions.addWidget(folder)
        actions.addWidget(refresh)
        self.root.addLayout(actions)
        self.player = AudioPlayer()
        self.root.addWidget(self.player)
        state.data_changed.connect(lambda what: self.refresh() if what in ("audio", "exports", "voices")
                                   and self.isVisible() else None)

    def show_kind(self, kind: str | None) -> None:
        """Open the page filtered to one kind (e.g. "export" from File → Exported Files)."""
        self._select_kind(kind)
        self.refresh()

    def _select_kind(self, kind: str | None) -> None:
        self.kind.setCurrentIndex(max(self.kind.findData(kind), 0))

    def refresh(self):
        self.run(audio_service.library, self._show, busy=False)

    def _show(self, items: list[dict]):
        self.items = items
        query = self.search.text().strip().lower()
        kind = self.kind.currentData()
        shown = [item for item in items if (kind is None or item["kind"] == kind) and
                 (not query or query in " ".join((item["name"], item["format"], item["path"])).lower())]
        present = [item for item in shown if item["exists"]]
        missing = len(shown) - len(present)
        size_mb = sum(item["file_size"] for item in present) / 1_048_576
        self.summary.setText(f"{len(shown)} file{'s' if len(shown) != 1 else ''} · {size_mb:.1f} MB"
                             + (f" · {missing} missing" if missing else ""))
        self.table.setRowCount(len(shown))
        for row, item in enumerate(shown):
            values = (item["name"], item["kind_label"], (item["format"] or "").upper(), format_duration(item["duration"]),
                      f"{item['file_size'] / 1_048_576:.1f} MB", _date(item["created_at"]), item["folder"],
                      "Found" if item["exists"] else "Missing")
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                cell.setData(Qt.ItemDataRole.UserRole, (item["kind"], item["id"]))
                if col in (0, 6):
                    cell.setToolTip(item["path"] + (f"\nUntouched original: {item['original_path']}"
                                                    if item.get("original_path") else ""))
                self.table.setItem(row, col, cell)

    def _current(self, must_exist: bool = False) -> dict | None:
        cell = self.table.item(self.table.currentRow(), 0)
        key = cell.data(Qt.ItemDataRole.UserRole) if cell is not None else None
        item = next((i for i in self.items if (i["kind"], i["id"]) == key), None)
        if item is None:
            self.error("Select a file first")
        elif must_exist and not Path(item["path"]).is_file():
            self.error(f"{item['file_name']} is no longer in {item['folder']}")
            return None
        return item

    def play(self):
        item = self._current(must_exist=True)
        if item:
            self.player.load(item["path"], item["name"])
            self.player.play()

    def open_in_editor(self):
        item = self._current()
        if not item:
            return
        if item["kind"] == "sample":
            self.error("Voice samples are managed on the Voices page.")
        elif not item["audios_id"]:  # an export whose source audio was deleted
            self.error("Its source audio is gone. Import the file to edit it (File → Import Audio File).")
        else:
            self.state.open_audio.emit(item["audios_id"])

    def show_in_folder(self):
        item = self._current()
        if not item:
            return
        path = Path(item["path"])
        if path.is_file() and sys.platform == "win32":
            subprocess.Popen(["explorer", f"/select,{path}"])
        elif path.is_file() and sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(path)])
        elif path.parent.is_dir():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.parent)))
        else:
            self.error(f"The folder {path.parent} no longer exists")

    def copy_path(self):
        item = self._current()
        if item:
            QGuiApplication.clipboard().setText(item["path"])

    def delete(self):
        item = self._current()
        if not item:
            return
        if item["kind"] == "sample":
            QMessageBox.information(self, "Voice samples", "Voice samples belong to their voice: remove them, or "
                                    "revoke the voice, on the Voices page so its consent record stays complete.")
            return
        if item["kind"] == "export":
            self._delete_export(item)
            return
        if QMessageBox.question(
            self, "Delete audio", f"Delete “{item['name']}” and its files? A script that uses it as a take loses "
            "that take.") == QMessageBox.StandardButton.Yes:
            self.player.load(None)  # Windows cannot delete a file that is open
            self.run(lambda: audio_service.delete(item["audios_id"]),
                     lambda _r: (self.state.notify("audio"), self.refresh()))

    def _delete_export(self, item: dict):
        box = QMessageBox(QMessageBox.Icon.Question, "Exported file", f"{item['path']}", parent=self)
        delete_file = box.addButton("Delete the file", QMessageBox.ButtonRole.DestructiveRole)
        box.addButton("Remove from the list", QMessageBox.ButtonRole.AcceptRole)
        box.addButton(QMessageBox.StandardButton.Cancel)
        box.exec()
        clicked = box.clickedButton()
        if clicked is None or box.buttonRole(clicked) == QMessageBox.ButtonRole.RejectRole:
            return
        body = ExportRequest(exports_id=item["id"], status=Status.DELETED.code, delete_file=clicked is delete_file)
        if body.delete_file:
            self.player.load(None)
        self.run(lambda: audio_service.save_export(body), lambda _r: self.refresh())


def _date(value: str | None) -> str:
    return local_display(datetime.fromisoformat(value)) if value else ""
