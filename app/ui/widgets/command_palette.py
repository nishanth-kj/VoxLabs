"""Command palette (Ctrl+Shift+P): search and run any menu command by name."""

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QAction, QKeyEvent
from PySide6.QtWidgets import QDialog, QLineEdit, QListWidget, QListWidgetItem, QMenu, QMenuBar, QVBoxLayout


def menu_commands(menu_bar: QMenuBar) -> list[tuple[str, QAction]]:
    """Every runnable action in the menu bar as ("Menu › Submenu › Command", action)."""
    found: list[tuple[str, QAction]] = []

    def walk(actions, path: list[str]):
        for action in actions:
            if action.isSeparator() or not action.isVisible():
                continue
            text = action.text().replace("&", "").split("\t")[0]
            menu = action.menu()
            if isinstance(menu, QMenu):
                walk(menu.actions(), [*path, text])
            elif text:
                found.append((" › ".join([*path, text]), action))

    walk(menu_bar.actions(), [])
    return found


def matches(label: str, query: str) -> bool:
    words = query.lower().split()
    return all(word in label.lower() for word in words)


class CommandPalette(QDialog):
    def __init__(self, menu_bar: QMenuBar, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("CommandPalette")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.commands = menu_commands(menu_bar)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Type a command, e.g. \"export\", \"clone\", \"theme\"…")
        self.list = QListWidget()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.addWidget(self.search)
        layout.addWidget(self.list)
        self.search.textChanged.connect(self.filter)
        self.search.returnPressed.connect(self.run_selected)
        self.list.itemActivated.connect(lambda _item: self.run_selected())
        self.search.installEventFilter(self)
        self.resize(560, 420)
        self.filter("")

    def filter(self, query: str) -> None:
        self.list.clear()
        for label, action in self.commands:
            if not matches(label, query):
                continue
            shortcut = action.shortcut().toString() or (action.text().split("\t")[1] if "\t" in action.text() else "")
            item = QListWidgetItem(f"{label}    {shortcut}".rstrip())
            item.setData(Qt.ItemDataRole.UserRole, action)
            if not action.isEnabled():
                item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.list.addItem(item)
        if self.list.count():
            self.list.setCurrentRow(0)

    def run_selected(self) -> None:
        item = self.list.currentItem()
        action = item.data(Qt.ItemDataRole.UserRole) if item else None
        self.accept()
        if isinstance(action, QAction) and action.isEnabled():
            action.trigger()

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.search and isinstance(event, QKeyEvent) and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Down, Qt.Key.Key_Up, Qt.Key.Key_PageDown, Qt.Key.Key_PageUp):
                self.list.keyPressEvent(event)
                return True
            if key == Qt.Key.Key_Escape:
                self.reject()
                return True
        return super().eventFilter(watched, event)

    def show_centered(self) -> None:
        parent = self.parentWidget()
        if parent is not None:
            top_left = parent.mapToGlobal(parent.rect().topLeft())
            self.move(top_left.x() + (parent.width() - self.width()) // 2, top_left.y() + 44)
        self.search.clear()
        self.show()
        self.search.setFocus()
