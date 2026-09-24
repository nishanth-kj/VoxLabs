from typing import cast

from PySide6.QtGui import QStandardItemModel
from PySide6.QtWidgets import QComboBox

from app.services.model_service import model_service


class ModelSelector(QComboBox):
    """Speech models; unusable ones are listed but disabled with a reason."""

    def __init__(self, parent=None, model_types: tuple[str, ...] | None = None,
                 default_label: str = "Default model", speaking_only: bool = True, only_usable: bool = True):
        super().__init__(parent)
        self.only_usable = only_usable  # False: list unusable models as selectable (Settings defaults)
        self.model_types = model_types
        self.default_label = default_label
        self.speaking_only = speaking_only
        self.setMinimumWidth(240)
        self.refresh()

    def refresh(self, preferred: str | None = None):
        current = self.model_key()
        self.blockSignals(True)
        self.clear()
        if self.default_label:
            self.addItem(self.default_label, None)
        for model in model_service.list_models(speaking_only=self.speaking_only):
            if self.model_types and model["model_type"] not in self.model_types:
                continue
            note = ""
            if not model["installed"]:
                note = " — not installed"
            elif not model["allowed"]:
                note = " — online (disabled)"
            elif model["online"]:
                note = " — online"
            self.addItem(model["name"] + note, model["key"])
            if self.only_usable and note and note != " — online":
                item = self._items().item(self.count() - 1)
                if item is not None:
                    item.setEnabled(False)
        self._select_usable(current, preferred)
        self.blockSignals(False)

    def _items(self) -> QStandardItemModel:
        return cast(QStandardItemModel, self.model())

    def _usable(self, index: int) -> bool:
        item = self._items().item(index)
        return index >= 0 and (item is None or item.isEnabled())

    def _select_usable(self, *keys: str | None):
        """Select the first usable key given, else the first enabled entry (never a disabled one)."""
        for key in keys:
            index = self.findData(key)
            if key is not None and self._usable(index):
                self.setCurrentIndex(index)
                return
        first = next((i for i in range(self.count()) if self._usable(i)), 0)
        self.setCurrentIndex(first)

    def model_key(self) -> str | None:
        return self.currentData()

    def set_model_key(self, key: str | None):
        if key is None and self.default_label:
            self.setCurrentIndex(0)
        else:
            self._select_usable(key)
