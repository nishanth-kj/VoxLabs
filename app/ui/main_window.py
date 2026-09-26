"""Main window (Electron / VS Code style): custom title bar with the full menu and a
command center, a collapsible icon sidebar, the page stack and a colored status bar.

Set `native_title_bar` in Settings to use the operating system's title bar instead;
the same menus then sit in a regular menu bar.
"""

import sys

from PySide6.QtCore import QEvent, QObject, QPoint, QSize, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication, QMouseEvent
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services.system_service import VERSION, system_service
from app.ui import icons, theme
from app.ui.app_menu import build_menu_bar, refresh_menu_icons
from app.ui.pages import BasePage
from app.ui.pages.clone_page import ClonePage
from app.ui.pages.editor_page import EditorPage
from app.ui.pages.generate_page import GeneratePage
from app.ui.pages.home_page import HomePage
from app.ui.pages.models_page import ModelsPage
from app.ui.pages.script_page import ScriptPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.studio_page import StudioPage
from app.ui.pages.voices_page import VoicesPage
from app.ui.widgets.audio_player import AudioPlayer
from app.ui.widgets.command_palette import CommandPalette, menu_commands
from app.ui.widgets.job_status import JobStatusWidget
from app.ui.widgets.nav_bar import NavBar
from app.ui.widgets.title_bar import TitleBar
from app.utils.files import PROJECT_ROOT, data_dir
from app.utils.logger import logger

RESIZE_MARGIN = 6


class AppState(QObject):
    """Small shared state: "something changed" notifications and navigation requests."""

    data_changed = Signal(str)  # "voices" | "audio" | "models" | "scripts" | "settings"
    open_audio = Signal(int)  # audios_id to open in the editor
    open_script = Signal(int)  # scripts_id to open on the Script page
    navigate = Signal(str)

    def notify(self, what: str):
        self.data_changed.emit(what)


# key, sidebar label, page class, icon
PAGES = [
    ("home", "Home", HomePage, "home"),
    ("studio", "Studio", StudioPage, "studio"),
    ("clone", "Clone Voice", ClonePage, "clone"),
    ("generate", "Generate", GeneratePage, "generate"),
    ("script", "Script to Audio", ScriptPage, "script"),
    ("editor", "Audio Editor", EditorPage, "editor"),
    ("voices", "Voices", VoicesPage, "voices"),
    ("models", "Models", ModelsPage, "models"),
    ("settings", "Settings", SettingsPage, "settings"),
]
NAV_SECTIONS = [("", ["home", "studio"]), ("Create", ["clone", "generate", "script", "editor"]),
                ("Library", ["voices", "models"])]
NAV_FOOTER = ["settings"]
EDIT_COMMANDS = ("undo", "redo", "cut", "copy", "paste", "delete", "select_all", "duplicate")


class MainWindow(QMainWindow):
    def __init__(self, native_title_bar: bool | None = None):
        super().__init__()
        if native_title_bar is None:
            native_title_bar = bool(system_service.get_setting("native_title_bar"))
        self.frameless = not native_title_bar
        if self.frameless:
            self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowTitle("VoxLabs")
        self.resize(1360, 860)
        self.setMinimumSize(QSize(980, 640))
        self.state = AppState()
        self._resize_filter_installed = False
        self._edge_cursor = False

        # Pages and navigation
        self.stack = QStackedWidget()
        self.pages: dict[str, BasePage] = {}
        labels = {key: (label, icon_name) for key, label, _cls, icon_name in PAGES}
        self.nav_items = [(key, label, icon_name) for key, label, _cls, icon_name in PAGES]
        for key, _label, cls, _icon in PAGES:
            page = cls(self.state)
            self.pages[key] = page
            self.stack.addWidget(page)
        self.nav = NavBar(
            [(title, [(key, *labels[key]) for key in keys]) for title, keys in NAV_SECTIONS],
            [(key, *labels[key]) for key in NAV_FOOTER],
        )
        self.nav.navigated.connect(self.go)

        # Menus: in the custom title bar, or in a regular menu bar with the system title bar
        self.theme_actions: dict[str, QAction] = {}
        self.api_action: QAction | None = None
        self.menu_bar = build_menu_bar(self)
        self.title_bar: TitleBar | None = None
        if self.frameless:
            self.title_bar = TitleBar(self.menu_bar)
            self.title_bar.command_center_clicked.connect(self.show_palette)
        else:
            self.setMenuBar(self.menu_bar)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body.addWidget(self.nav)
        body.addWidget(self.stack, 1)
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if self.title_bar is not None:
            layout.addWidget(self.title_bar)
        layout.addLayout(body, 1)
        self.setCentralWidget(central)

        # Status bar: API and background jobs
        status = self.statusBar()
        status.setSizeGripEnabled(False)
        self.api_button = QPushButton()
        self.api_button.setToolTip("Start or stop the REST API and MCP server")
        self.api_button.clicked.connect(lambda: self.toggle_api(not system_service.api_running()))
        self.jobs_widget = JobStatusWidget()
        status.addWidget(self.api_button)
        status.addPermanentWidget(self.jobs_widget)

        self.state.navigate.connect(self.go)
        self.state.open_audio.connect(lambda _id: self.go("editor"))
        self.state.open_script.connect(lambda _id: self.go("script"))
        self.state.data_changed.connect(lambda what: self._settings_changed() if what == "settings" else None)
        QGuiApplication.styleHints().colorSchemeChanged.connect(lambda _scheme: self._follow_system_theme())

        if system_service.get_setting("sidebar_collapsed"):
            self.nav.set_collapsed(True)
        theme.polish_views(self)
        self._check_theme_action()
        self._update_api_status()
        self.go("home")
        # Autosave the editor state periodically when enabled.
        self._autosave = QTimer(self)
        self._autosave.timeout.connect(self._autosave_tick)
        self._autosave.start(30_000)

    # ------------------------------------------------------------ navigation and commands

    def go(self, key: str):
        page = self.pages.get(key)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        self.nav.select(key)
        self._update_titles()
        logger.debug(f"Page: {page.title}")
        page.refresh()

    def current_key(self) -> str:
        page = self.stack.currentWidget()
        return next((key for key, p in self.pages.items() if p is page), "home")

    def command(self, key: str, method: str, *args) -> None:
        """Open a page and run one of its commands (used by the menus and the command palette)."""
        self.go(key)
        page = self.pages[key]
        try:
            getattr(page, method)(*args)
        except Exception as exc:
            logger.error(f"Command {key}.{method} failed", exc_info=exc)
            page.error(exc)

    def edit_command(self, name: str) -> None:
        """Edit menu: act on the focused text box, otherwise on the audio editor."""
        focus = QApplication.focusWidget()
        ops = {}
        if isinstance(focus, QLineEdit):
            ops = {"undo": focus.undo, "redo": focus.redo, "cut": focus.cut, "copy": focus.copy,
                   "paste": focus.paste, "delete": focus.del_, "select_all": focus.selectAll}
        elif isinstance(focus, (QTextEdit, QPlainTextEdit)):
            box = focus
            ops = {"undo": box.undo, "redo": box.redo, "cut": box.cut, "copy": box.copy, "paste": box.paste,
                   "delete": lambda: box.textCursor().removeSelectedText(), "select_all": box.selectAll}
        if name in ops:
            ops[name]()
        elif name in EDIT_COMMANDS:
            self.command("editor", name)

    def show_palette(self) -> None:
        CommandPalette(self.menu_bar, self).show_centered()

    def show_jobs(self) -> None:
        self.jobs_widget.open_dialog()

    def open_data_folder(self) -> None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(data_dir())))

    def open_docs(self) -> None:
        docs = PROJECT_ROOT / "docs"
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(docs if docs.exists() else PROJECT_ROOT)))

    def show_about(self) -> None:
        QMessageBox.about(
            self, "About VoxLabs",
            f"<h3>VoxLabs {VERSION}</h3>"
            "<p>Local-first voice cloning, text-to-speech and audio production.</p>"
            "<p>Generated audio is labeled as AI-generated. Cloning a voice requires the speaker's "
            "recorded consent, and revoking a voice deletes its samples.</p>",
        )

    def shortcut_rows(self) -> list[tuple[str, str]]:
        rows = []
        for label, action in menu_commands(self.menu_bar):
            shortcut = action.shortcut().toString() or (action.text().split("\t")[1] if "\t" in action.text() else "")
            if shortcut:
                rows.append((label, shortcut))
        return rows

    def show_shortcuts(self) -> None:
        rows = self.shortcut_rows()
        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts")
        dialog.resize(560, 560)
        table = QTableWidget(len(rows), 2)
        table.setHorizontalHeaderLabels(["Command", "Shortcut"])
        table.verticalHeader().hide()
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        for row, (label, shortcut) in enumerate(rows):
            table.setItem(row, 0, QTableWidgetItem(label))
            table.setItem(row, 1, QTableWidgetItem(shortcut))
        QVBoxLayout(dialog).addWidget(table)
        theme.polish_views(dialog)
        dialog.exec()

    # ------------------------------------------------------------ view

    def toggle_sidebar(self) -> None:
        self.nav.set_collapsed(not self.nav.collapsed)
        collapsed = self.nav.collapsed
        self.pages["settings"].run(lambda: system_service.update_settings(sidebar_collapsed=collapsed), busy=False)

    def toggle_full_screen(self) -> None:
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def set_theme(self, mode: str) -> None:
        app = QApplication.instance()
        if isinstance(app, QApplication):
            theme.apply_theme(app, mode)
        self.refresh_icons()
        self._check_theme_action(mode)
        self.pages["settings"].run(lambda: system_service.update_settings(theme=mode), busy=False)

    def _settings_changed(self) -> None:
        """Settings were saved (possibly on the Settings page): apply the theme and refresh the status bar."""
        mode = system_service.get_setting("theme") or "system"
        app = QApplication.instance()
        if theme.resolve(mode) is not theme.current() and isinstance(app, QApplication):
            theme.apply_theme(app, mode)
            self.refresh_icons()
        self._check_theme_action(mode)
        self._update_api_status()

    def _follow_system_theme(self) -> None:
        if (system_service.get_setting("theme") or "system") == "system":
            self.set_theme("system")

    def _check_theme_action(self, mode: str | None = None) -> None:
        mode = mode or system_service.get_setting("theme") or "system"
        if mode in self.theme_actions:
            self.theme_actions[mode].setChecked(True)

    def refresh_icons(self) -> None:
        """Re-render every icon in the current theme's colors."""
        self.nav.refresh_icons()
        if self.title_bar is not None:
            self.title_bar.refresh_icons()
        refresh_menu_icons(self.menu_bar)
        for page in self.pages.values():
            page.refresh_icons()
            page.update()
        for player in self.findChildren(AudioPlayer):
            player.refresh_icons()
        self._update_titles()
        self._update_api_status()

    # ------------------------------------------------------------ status

    def toggle_api(self, enabled: bool | None = None) -> None:
        if enabled is None:
            enabled = self.api_action.isChecked() if self.api_action else not system_service.api_running()

        def apply():
            system_service.update_settings(api_enabled=enabled)
            system_service.apply_api_setting()

        self.pages["settings"].run(apply, lambda _r: (self._update_api_status(), self.state.notify("settings")),
                                   on_error=self._update_api_status)

    def _update_api_status(self) -> None:
        running = system_service.api_running()
        if running:
            settings = system_service.get_settings()
            self.api_button.setText(f"API + MCP  {settings['api_host']}:{settings['api_port']}")
        else:
            self.api_button.setText("API off")
        self.api_button.setIcon(icons.icon("api", theme.current().statusbar_text, size=14))
        if self.api_action is not None:
            self.api_action.setChecked(running)

    def _update_titles(self) -> None:
        page = self.stack.currentWidget()
        page_title = page.title if isinstance(page, BasePage) else ""
        self.setWindowTitle(f"VoxLabs — {page_title}" if page_title else "VoxLabs")
        if self.title_bar is not None:
            self.title_bar.set_title(f"{page_title}  ·  Search commands")

    # ------------------------------------------------------------ frameless window: resizing from the edges

    def showEvent(self, event):
        super().showEvent(event)
        handle = self.windowHandle()
        if self.frameless and handle is not None and not self._resize_filter_installed:
            handle.installEventFilter(self)
            self._resize_filter_installed = True
            _round_corners(self)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange and self.title_bar is not None:
            self.title_bar.refresh_icons(self.isMaximized())
        super().changeEvent(event)

    def _edges_at(self, pos: QPoint) -> Qt.Edge:
        edges = Qt.Edge(0)
        if self.isMaximized() or self.isFullScreen():
            return edges
        if pos.x() <= RESIZE_MARGIN:
            edges |= Qt.Edge.LeftEdge
        elif pos.x() >= self.width() - RESIZE_MARGIN:
            edges |= Qt.Edge.RightEdge
        if pos.y() <= RESIZE_MARGIN:
            edges |= Qt.Edge.TopEdge
        elif pos.y() >= self.height() - RESIZE_MARGIN:
            edges |= Qt.Edge.BottomEdge
        return edges

    def _set_edge_cursor(self, edges: Qt.Edge) -> None:
        if edges == Qt.Edge(0):
            if self._edge_cursor:
                QApplication.restoreOverrideCursor()
                self._edge_cursor = False
            return
        horizontal = bool(edges & (Qt.Edge.LeftEdge | Qt.Edge.RightEdge))
        vertical = bool(edges & (Qt.Edge.TopEdge | Qt.Edge.BottomEdge))
        if horizontal and vertical:
            forward = edges in (Qt.Edge.LeftEdge | Qt.Edge.TopEdge, Qt.Edge.RightEdge | Qt.Edge.BottomEdge)
            shape = Qt.CursorShape.SizeFDiagCursor if forward else Qt.CursorShape.SizeBDiagCursor
        else:
            shape = Qt.CursorShape.SizeHorCursor if horizontal else Qt.CursorShape.SizeVerCursor
        if self._edge_cursor:
            QApplication.changeOverrideCursor(shape)
        else:
            QApplication.setOverrideCursor(shape)
            self._edge_cursor = True

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if watched is self.windowHandle():
            if isinstance(event, QMouseEvent):
                edges = self._edges_at(event.position().toPoint())
                if event.type() == QEvent.Type.MouseMove and not event.buttons():
                    self._set_edge_cursor(edges)
                elif event.type() == QEvent.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
                    handle = self.windowHandle()
                    if edges != Qt.Edge(0) and handle is not None:
                        handle.startSystemResize(edges)
                        return True
            elif event.type() == QEvent.Type.Leave:
                self._set_edge_cursor(Qt.Edge(0))
        return super().eventFilter(watched, event)

    # ------------------------------------------------------------ autosave

    def _autosave_editor(self):
        editor = self.pages["editor"]
        if isinstance(editor, EditorPage):
            editor.autosave()

    def _autosave_tick(self):
        if system_service.get_setting("autosave"):
            self._autosave_editor()

    def closeEvent(self, event):
        self._autosave_editor()
        super().closeEvent(event)


def _round_corners(window: QWidget) -> None:
    """Ask Windows 11 to round the corners of the frameless window (ignored elsewhere)."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        preference = ctypes.c_int(2)  # DWMWCP_ROUND
        ctypes.windll.dwmapi.DwmSetWindowAttribute(  # type: ignore[attr-defined]
            int(window.winId()), 33, ctypes.byref(preference), ctypes.sizeof(preference))  # corner preference
    except Exception:
        pass
