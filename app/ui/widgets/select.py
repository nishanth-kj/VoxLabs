"""The app's select (dropdown). Use `Select` instead of QComboBox, and `choose_item` instead of
QInputDialog.getItem, so every select looks and works the same:

- the list opens below the box, or above it when there is no room, never over the current item;
- it is a rounded list on a transparent window (no square or black backdrop);
- its first row is a search box: click it or just start typing, Up/Down/Enter pick a match.

The look and behaviour live in `theme.polish_combo_popup`.
"""

from collections.abc import Sequence

from PySide6.QtWidgets import QComboBox, QInputDialog, QWidget

from app.ui import theme


class Select(QComboBox):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        theme.polish_combo_popup(self)


def choose_item(parent: QWidget, title: str, label: str, items: Sequence[str], current: int = 0) -> str | None:
    """Ask for one of `items` in a small dialog whose select works like every other one; None if cancelled."""
    dialog = QInputDialog(parent)
    dialog.setWindowTitle(title)
    dialog.setLabelText(label)
    dialog.setComboBoxItems(list(items))  # creates the dialog's select
    dialog.setComboBoxEditable(False)
    if items:
        dialog.setTextValue(items[max(0, min(current, len(items) - 1))])
    theme.polish_views(dialog)
    return dialog.textValue() if dialog.exec() else None
