from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QCompleter, QFrame, QLineEdit, QSizePolicy, QVBoxLayout, QWidget

from app.services.model_service import model_service
from app.services.system_service import system_service
from app.services.voice_service import voice_service


def _polish_popup(combo: QComboBox) -> None:
    """Keep the open list a fixed row height so the last voice is not cut off."""
    combo.setMaxVisibleItems(12)
    view = combo.view()
    view.setUniformItemSizes(True)
    view.setSpacing(0)
    view.setFrameShape(QFrame.Shape.NoFrame)
    view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    view.setTextElideMode(Qt.TextElideMode.ElideRight)
    view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)


def voice_matches(voice: dict, query: str, model_key: str | None, *, allow_edge: bool | None = None) -> bool:
    """True when a voice passes the Microsoft Edge switch, the model filter, and the search text."""
    if allow_edge is None:
        allow_edge = bool(system_service.get_setting("allow_edge"))
    if not allow_edge and voice.get("model_key") == "edge-neural":
        return False
    if model_key and voice.get("model_key") != model_key:
        return False
    text = query.strip().lower()
    if not text:
        return True
    haystack = " ".join(
        str(voice.get(key) or "") for key in ("name", "engine_voice", "language", "model_key", "description")
    ).lower()
    return text in haystack


class VoiceSelector(QWidget):
    """Voice picker with a text search and a model filter.

    `filters=False` keeps only the combo, for tight rows such as a speaker table.
    Typing in the combo still searches, and Microsoft Edge stays hidden while its setting is off.
    """

    currentIndexChanged = Signal(int)

    def __init__(self, parent=None, none_label: str = "Engine default voice", *, filters: bool = True):
        super().__init__(parent)
        self.none_label = none_label
        self._filters = filters
        self._voices: list[dict] = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search voices")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(lambda _text: self._fill())
        self.model_filter = QComboBox()
        self.model_filter.currentIndexChanged.connect(lambda _i: self._fill())
        self.search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.model_filter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if filters:
            layout.addWidget(self.search)
            layout.addWidget(self.model_filter)
        else:
            self.search.hide()
            self.model_filter.hide()

        self.combo = QComboBox()
        self.combo.setMinimumWidth(0)
        self.combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        if filters:
            self.combo.setEditable(True)
            self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
            completer = QCompleter(self.combo.model(), self)
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
            completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.combo.setCompleter(completer)
        self.combo.currentIndexChanged.connect(self.currentIndexChanged.emit)
        layout.addWidget(self.combo)
        _polish_popup(self.model_filter)
        _polish_popup(self.combo)
        self.refresh()

    def refresh(self):
        current = self.voices_id()
        model_key = self.model_filter.currentData() if self.model_filter.count() else None
        self._voices = voice_service.list_voices()
        names = {}
        for model in model_service.list_models(speaking_only=False):
            names[model["key"]] = model["name"]
        self.model_filter.blockSignals(True)
        self.model_filter.clear()
        self.model_filter.addItem("All models", None)
        seen = []
        for voice in self._voices:
            key = voice.get("model_key")
            if key and key not in seen and voice_matches(voice, "", None):
                seen.append(key)
                self.model_filter.addItem(names.get(key, key), key)
        index = self.model_filter.findData(model_key)
        self.model_filter.setCurrentIndex(index if index >= 0 else 0)
        self.model_filter.blockSignals(False)
        self._fill(current)

    def _fill(self, keep: int | None = None):
        if keep is None:
            keep = self.voices_id()
        query = self.search.text()
        model_key = self.model_filter.currentData()
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItem(self.none_label, None)
        for voice in self._voices:
            if not voice_matches(voice, query, model_key):
                continue
            kind = "cloned" if voice["source"] == "clone" else "preset"
            self.combo.addItem(f"{voice['name']}  ({kind})", voice["voices_id"])
        self.combo.blockSignals(False)
        self.set_voices_id(keep)

    def voices_id(self) -> int | None:
        return self.combo.currentData()

    def set_model_filter(self, model_key: str | None):
        """Show only voices bound to this model. `None` shows every voice."""
        if model_key and self.model_filter.findData(model_key) < 0:
            name = model_key
            for model in model_service.list_models(speaking_only=False):
                if model["key"] == model_key:
                    name = model["name"]
                    break
            self.model_filter.addItem(name, model_key)
        index = self.model_filter.findData(model_key)
        self.model_filter.setCurrentIndex(index if index >= 0 else 0)

    def set_voices_id(self, voices_id: int | None):
        index = self.combo.findData(voices_id)
        self.combo.setCurrentIndex(index if index >= 0 else 0)
