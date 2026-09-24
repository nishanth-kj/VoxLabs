from PySide6.QtWidgets import QComboBox

from app.services.voice_service import voice_service


class VoiceSelector(QComboBox):
    """Voices from VoiceService; the first entry means "engine default voice"."""

    def __init__(self, parent=None, none_label: str = "Engine default voice"):
        super().__init__(parent)
        self.none_label = none_label
        self.setMinimumWidth(200)
        self.refresh()

    def refresh(self):
        current = self.voices_id()
        self.blockSignals(True)
        self.clear()
        self.addItem(self.none_label, None)
        for voice in voice_service.list_voices():
            kind = "cloned" if voice["source"] == "clone" else "preset"
            self.addItem(f"{voice['name']}  ({kind})", voice["voices_id"])
        self.set_voices_id(current)
        self.blockSignals(False)

    def voices_id(self) -> int | None:
        return self.currentData()

    def set_voices_id(self, voices_id: int | None):
        index = self.findData(voices_id)
        self.setCurrentIndex(index if index >= 0 else 0)
