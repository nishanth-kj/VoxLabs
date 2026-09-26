"""Custom title bar (Electron / VS Code style): logo, menus, command center and window buttons.

Dragging the empty area moves the window (native move, so Windows snapping works);
double-clicking it maximizes or restores.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMenuBar, QPushButton, QWidget

from app.ui import icons

TITLE_BAR_HEIGHT = 38


class TitleBar(QWidget):
    command_center_clicked = Signal()

    def __init__(self, menu_bar: QMenuBar, show_window_buttons: bool = True, parent=None):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedHeight(TITLE_BAR_HEIGHT)

        self.logo = QLabel()
        self.logo.setFixedSize(30, TITLE_BAR_HEIGHT)
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name = QLabel("VoxLabs")
        name.setObjectName("AppName")
        self.menu_bar = menu_bar
        self.command_center = QPushButton()
        self.command_center.setObjectName("CommandCenter")
        self.command_center.setCursor(Qt.CursorShape.PointingHandCursor)
        self.command_center.setToolTip("Search all commands (Ctrl+Shift+P)")
        self.command_center.clicked.connect(self.command_center_clicked)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self.logo)
        layout.addWidget(name)
        layout.addWidget(menu_bar)
        layout.addStretch(1)
        layout.addWidget(self.command_center)
        layout.addStretch(1)

        self.window_buttons: dict[str, QPushButton] = {}
        if show_window_buttons:
            for key, tip in (("minimize", "Minimize"), ("maximize", "Maximize"), ("close", "Close")):
                button = QPushButton()
                button.setObjectName("CloseButton" if key == "close" else "WindowButton")
                button.setToolTip(tip)
                button.setIconSize(icons.ICON_SIZE)
                button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                layout.addWidget(button)
                self.window_buttons[key] = button
            self.window_buttons["minimize"].clicked.connect(lambda: self.window().showMinimized())
            self.window_buttons["maximize"].clicked.connect(self.toggle_maximized)
            self.window_buttons["close"].clicked.connect(lambda: self.window().close())
        self.refresh_icons()

    def set_title(self, text: str) -> None:
        self.command_center.setText(f"  {text}")

    def toggle_maximized(self) -> None:
        window = self.window()
        window.showNormal() if window.isMaximized() else window.showMaximized()

    def refresh_icons(self, maximized: bool | None = None) -> None:
        self.logo.setPixmap(icons.pixmap("logo", "#ffffff", 20))
        self.command_center.setIcon(icons.icon("search"))
        if not self.window_buttons:
            return
        maximized = self.window().isMaximized() if maximized is None else maximized
        self.window_buttons["minimize"].setIcon(icons.icon("minimize"))
        self.window_buttons["maximize"].setIcon(icons.icon("restore" if maximized else "maximize"))
        self.window_buttons["maximize"].setToolTip("Restore" if maximized else "Maximize")
        self.window_buttons["close"].setIcon(icons.icon("close"))

    # ------------------------------------------------------------ dragging

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.window_buttons:
            handle = self.window().windowHandle()
            if handle is not None:
                handle.startSystemMove()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.window_buttons:
            self.toggle_maximized()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
