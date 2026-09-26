"""Voices: preview, rename, edit, add sample, revoke and delete."""

import json
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
)

from app.constants.models import EDGE_DEFAULT_VOICE
from app.services.clone_service import clone_service
from app.services.voice_service import voice_service
from app.ui.pages import BasePage
from app.ui.pages.clone_page import AUDIO_FILTER
from app.ui.widgets.audio_player import AudioPlayer
from app.ui.widgets.model_selector import ModelSelector
from app.utils.time import local_display

COLUMNS = ("Name", "Type", "Samples", "Consent", "Status", "Language", "Created", "Updated")


class VoiceEditDialog(QDialog):
    def __init__(self, voice: dict | None = None, parent=None, preset: bool = False):
        super().__init__(parent)
        self.setWindowTitle("Edit voice" if voice else "New preset voice")
        voice = voice or {}
        self.name = QLineEdit(voice.get("name", ""))
        self.description = QLineEdit(voice.get("description", ""))
        self.language = QLineEdit(voice.get("language", "en"))
        form = QFormLayout(self)
        form.addRow("Name", self.name)
        form.addRow("Description", self.description)
        form.addRow("Language", self.language)
        self.engine_voice: QLineEdit | None = None
        self.model: ModelSelector | None = None
        if preset or voice.get("source") == "preset":
            self.model = ModelSelector(default_label="Default model")
            self.model.set_model_key(voice.get("model_key"))
            self.engine_voice = QLineEdit(voice.get("engine_voice") or EDGE_DEFAULT_VOICE)
            self.engine_voice.setToolTip("Engine speaker id, e.g. an Edge voice such as en-GB-RyanNeural")
            form.addRow("Model", self.model)
            form.addRow("Engine voice", self.engine_voice)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def values(self) -> dict:
        values: dict[str, str | None] = {"name": self.name.text(), "description": self.description.text(),
                                         "language": self.language.text().strip() or "en"}
        if self.model is not None and self.engine_voice is not None:
            values["model_key"] = self.model.model_key()
            values["engine_voice"] = self.engine_voice.text().strip() or None
        return values


class VoicesPage(BasePage):
    title = "Voices"
    subtitle = "Cloned and preset voices. Revoking a voice deletes its samples immediately."

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.voices: list[dict] = []
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.itemDoubleClicked.connect(lambda _i: self.preview())
        self.root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        for label, slot in (("Preview", self.preview), ("Rename", self.rename), ("Edit", self.edit),
                            ("Add sample", self.add_sample), ("Export metadata", self.export_metadata),
                            ("Revoke", self.revoke), ("Delete", self.delete)):
            button = QPushButton(label)
            button.clicked.connect(slot)
            actions.addWidget(button)
        actions.addStretch()
        new_clone = QPushButton("Clone new voice")
        new_clone.clicked.connect(lambda: state.navigate.emit("clone"))
        new_preset = QPushButton("New preset voice")
        new_preset.clicked.connect(self.new_preset)
        actions.addWidget(new_preset)
        actions.addWidget(new_clone)
        self.root.addLayout(actions)
        self.player = AudioPlayer()
        self.root.addWidget(self.player)
        state.data_changed.connect(lambda what: self.refresh() if what == "voices" and self.isVisible() else None)

    def refresh(self):
        self.run(lambda: voice_service.list_voices(include_revoked=True), self._show, busy=False)

    def _show(self, voices):
        self.voices = voices
        self.table.setRowCount(len(voices))
        for row, voice in enumerate(voices):
            values = (voice["name"], "Cloned" if voice["source"] == "clone" else "Preset", str(voice["sample_count"]),
                      voice["consent_status_label"], voice["status_label"], voice["language"],
                      _date(voice["created_at"]), _date(voice["updated_at"]))
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.ItemDataRole.UserRole, voice["voices_id"])
                self.table.setItem(row, col, item)

    def _current(self) -> dict | None:
        row = self.table.currentRow()
        if 0 <= row < len(self.voices):
            return self.voices[row]
        self.error("Select a voice first")
        return None

    def _changed(self, _result=None):
        self.state.notify("voices")
        self.refresh()

    def preview(self):
        voice = self._current()
        if not voice:
            return
        job = clone_service.preview_async(voice["voices_id"])
        self.follow(job, lambda r: (self.player.load(r["audio"]["path"], f"Preview · {voice['name']}"),
                                    self.player.play()))

    def rename(self):
        voice = self._current()
        if voice:
            name, ok = QInputDialog.getText(self, "Rename voice", "Name:", text=voice["name"])
            if ok:
                self.run(lambda: voice_service.rename(voice["voices_id"], name), self._changed)

    def edit(self):
        voice = self._current()
        if voice:
            dialog = VoiceEditDialog(voice, self)
            if dialog.exec():
                values = dialog.values()
                self.run(lambda: voice_service.update(voice["voices_id"], **values), self._changed)

    def new_preset(self):
        dialog = VoiceEditDialog(None, self, preset=True)
        if dialog.exec():
            values = dialog.values()
            self.run(lambda: voice_service.create(**values), self._changed)

    def add_sample(self):
        voice = self._current()
        if voice:
            path, _ = QFileDialog.getOpenFileName(self, "Add sample", "", AUDIO_FILTER)
            if path:
                self.run(lambda: voice_service.attach_sample(voice["voices_id"], path), self._changed)

    def export_metadata(self):
        voice = self._current()
        if voice:
            path, _ = QFileDialog.getSaveFileName(self, "Export voice metadata", f"{voice['name']}.json", "*.json")
            if path:
                def write():
                    with open(path, "w", encoding="utf-8") as fh:
                        json.dump(voice_service.export_metadata(voice["voices_id"]), fh, indent=2, default=str)
                self.run(write)

    def revoke(self):
        voice = self._current()
        if voice and QMessageBox.question(
            self, "Revoke voice",
            f"Revoke “{voice['name']}”? Its samples and voice profile are deleted immediately and it can no "
            "longer be used. The consent record is kept marked as revoked.",
        ) == QMessageBox.StandardButton.Yes:
            self.run(lambda: voice_service.revoke(voice["voices_id"]), self._changed)

    def delete(self):
        voice = self._current()
        if voice and QMessageBox.question(
            self, "Delete voice", f"Permanently delete “{voice['name']}”, its samples and consent records?"
        ) == QMessageBox.StandardButton.Yes:
            self.run(lambda: voice_service.delete(voice["voices_id"]), self._changed)


def _date(value: str | None) -> str:
    return local_display(datetime.fromisoformat(value)) if value else ""
