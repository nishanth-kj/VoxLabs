"""Main window: sidebar navigation, page stack and the job status bar."""

from PySide6.QtCore import QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from app.services.project_service import project_service
from app.services.system_service import VERSION, system_service
from app.utils.logger import logger
from app.ui.pages import BasePage
from app.ui.pages.clone_page import ClonePage
from app.ui.pages.editor_page import EditorPage
from app.ui.pages.generate_page import GeneratePage
from app.ui.pages.home_page import HomePage
from app.ui.pages.models_page import ModelsPage
from app.ui.pages.projects_page import ProjectsPage
from app.ui.pages.script_page import ScriptPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.studio_page import StudioPage
from app.ui.pages.voices_page import VoicesPage
from app.ui.widgets.job_status import JobStatusWidget

STYLE = """
#Sidebar { border: none; font-size: 14px; padding-top: 8px; }
#Sidebar::item { padding: 9px 14px; border-radius: 6px; margin: 1px 6px; }
#PageTitle { font-size: 20px; font-weight: 600; padding-bottom: 6px; }
#Hint { color: #8a8a8a; }
#Banner { background: palette(alternate-base); border: 1px solid palette(mid); border-radius: 6px; padding: 8px; }
QGroupBox { font-weight: 600; margin-top: 10px; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
"""


class AppState(QObject):
    """Small shared state: the open project and "something changed" notifications."""

    project_changed = Signal(object)  # projects_id | None
    data_changed = Signal(str)  # "voices" | "audio" | "models" | "projects" | "scripts" | "settings"
    open_audio = Signal(int)  # audios_id to open in the editor
    open_script = Signal(int)  # scripts_id to open on the Script page
    navigate = Signal(str)

    def __init__(self):
        super().__init__()
        self.projects_id: int | None = None

    def set_project(self, projects_id: int | None):
        self.projects_id = projects_id
        self.project_changed.emit(projects_id)

    def project_name(self) -> str:
        if self.projects_id is None:
            return "No project"
        try:
            return project_service.get(self.projects_id)["name"]
        except Exception:
            return "No project"

    def notify(self, what: str):
        self.data_changed.emit(what)


PAGES = [
    ("home", "Home", HomePage),
    ("studio", "Studio", StudioPage),
    ("clone", "Clone Voice", ClonePage),
    ("generate", "Generate Audio", GeneratePage),
    ("script", "Script to Audio", ScriptPage),
    ("editor", "Audio Editor", EditorPage),
    ("voices", "Voices", VoicesPage),
    ("projects", "Projects", ProjectsPage),
    ("models", "Models", ModelsPage),
    ("settings", "Settings", SettingsPage),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"VoxLabs {VERSION}")
        self.resize(1320, 840)
        self.setMinimumSize(QSize(960, 620))
        self.setStyleSheet(STYLE)
        self.state = AppState()

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(190)
        self.sidebar.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.stack = QStackedWidget()
        self.pages: dict[str, BasePage] = {}
        for key, label, cls in PAGES:
            page = cls(self.state)
            self.pages[key] = page
            self.stack.addWidget(page)
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.sidebar.addItem(item)
        self.sidebar.currentRowChanged.connect(self._show_row)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.project_label = QLabel()
        self.statusBar().addWidget(self.project_label)
        self.statusBar().addPermanentWidget(JobStatusWidget())
        self.state.project_changed.connect(lambda _p: self._update_project_label())
        self.state.navigate.connect(self.go)
        self.state.open_audio.connect(lambda _id: self.go("editor"))
        self.state.open_script.connect(lambda _id: self.go("script"))
        self._update_project_label()

        for index, (key, _label, _cls) in enumerate(PAGES[:9]):
            action = QAction(self)
            action.setShortcut(QKeySequence(f"Ctrl+{index + 1}"))
            action.triggered.connect(lambda _checked=False, k=key: self.go(k))
            self.addAction(action)

        self.sidebar.setCurrentRow(0)
        # Autosave the editor state periodically when enabled.
        self._autosave = QTimer(self)
        self._autosave.timeout.connect(self._autosave_tick)
        self._autosave.start(30_000)

    def go(self, key: str):
        for row in range(self.sidebar.count()):
            if self.sidebar.item(row).data(Qt.ItemDataRole.UserRole) == key:
                self.sidebar.setCurrentRow(row)
                return

    def _show_row(self, row: int):
        self.stack.setCurrentIndex(row)
        page = self.stack.currentWidget()
        if isinstance(page, BasePage):
            logger.debug(f"Page: {page.title}")
            page.refresh()

    def _update_project_label(self):
        self.project_label.setText(f"Project: {self.state.project_name()}")

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
