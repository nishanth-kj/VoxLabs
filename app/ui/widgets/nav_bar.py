"""Left navigation: icon + label buttons grouped in sections, collapsible to icons only."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QButtonGroup, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui import icons, theme

EXPANDED_WIDTH = 208
COLLAPSED_WIDTH = 58


class NavBar(QWidget):
    navigated = Signal(str)

    def __init__(self, sections: list[tuple[str, list[tuple[str, str, str]]]],
                 footer: list[tuple[str, str, str]], parent=None):
        """`sections` is [(section title, [(key, label, icon name), ...]), ...]; `footer` sits at the bottom."""
        super().__init__(parent)
        self.setObjectName("NavBar")
        self.collapsed = False
        self.buttons: dict[str, QPushButton] = {}
        self._labels: dict[str, str] = {}
        self._icons: dict[str, str] = {}
        self._section_labels: list[QLabel] = []
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)
        for title, items in sections:
            if title:
                label = QLabel(title.upper())
                label.setObjectName("NavSection")
                self._section_labels.append(label)
                layout.addWidget(label)
            for key, text, icon_name in items:
                layout.addWidget(self._button(key, text, icon_name))
        layout.addStretch(1)
        for key, text, icon_name in footer:
            layout.addWidget(self._button(key, text, icon_name))
        self.toggle_button = QPushButton()
        self.toggle_button.setObjectName("NavToggle")
        self.toggle_button.setIconSize(icons.ICON_SIZE)
        self.toggle_button.clicked.connect(lambda: self.set_collapsed(not self.collapsed))
        layout.addWidget(self.toggle_button)
        self.setFixedWidth(EXPANDED_WIDTH)
        self.refresh_icons()

    def _button(self, key: str, text: str, icon_name: str) -> QPushButton:
        button = QPushButton(text)
        button.setCheckable(True)
        button.setIconSize(icons.ICON_SIZE)
        button.setToolTip(text)
        button.clicked.connect(lambda _checked=False, k=key: self.navigated.emit(k))
        self._group.addButton(button)
        self.buttons[key] = button
        self._labels[key] = text
        self._icons[key] = icon_name
        return button

    def select(self, key: str) -> None:
        if key in self.buttons:
            self.buttons[key].setChecked(True)

    def set_collapsed(self, collapsed: bool) -> None:
        self.collapsed = collapsed
        for key, button in self.buttons.items():
            button.setText("" if collapsed else self._labels[key])
        for label in self._section_labels:
            label.setVisible(not collapsed)
        self.setFixedWidth(COLLAPSED_WIDTH if collapsed else EXPANDED_WIDTH)
        self.refresh_icons()

    def refresh_icons(self) -> None:
        accent = theme.current().accent
        for key, button in self.buttons.items():
            button.setIcon(icons.icon(self._icons[key], checked=accent))
        self.toggle_button.setIcon(icons.icon("chevron_right" if self.collapsed else "chevron_left"))
        self.toggle_button.setText("" if self.collapsed else "Collapse")
        self.toggle_button.setToolTip("Expand sidebar (Ctrl+B)" if self.collapsed else "Collapse sidebar (Ctrl+B)")
