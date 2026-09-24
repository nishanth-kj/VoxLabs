from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QGroupBox, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout

from app.services.audio_service import audio_service
from app.services.job_service import job_service
from app.services.model_service import model_service
from app.services.project_service import project_service
from app.services.voice_service import voice_service
from app.ui.pages import BasePage
from app.ui.widgets.progress import JobBridge
from app.utils.time import format_duration


class HomePage(BasePage):
    title = "Home"

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.banner = QLabel()
        self.banner.setObjectName("Banner")
        self.banner.setWordWrap(True)
        self.banner.hide()
        self.root.addWidget(self.banner)

        actions = QHBoxLayout()
        for label, target in (("Clone Voice", "clone"), ("Generate Speech", "generate"),
                              ("Create Script Audio", "script"), ("Open Audio Editor", "editor")):
            button = QPushButton(label)
            button.setMinimumHeight(40)
            button.clicked.connect(lambda _c=False, t=target: state.navigate.emit(t))
            actions.addWidget(button)
        new_project = QPushButton("New Project")
        new_project.setMinimumHeight(40)
        new_project.clicked.connect(lambda: state.navigate.emit("projects"))
        actions.addWidget(new_project)
        self.root.addLayout(actions)

        grid = QGridLayout()
        self.projects = self._list(grid, "Recent Projects", 0, 0, self._open_project)
        self.voices = self._list(grid, "Recent Voices", 0, 1, lambda _i: state.navigate.emit("voices"))
        self.audio = self._list(grid, "Recent Audio", 0, 2, self._open_audio)
        self.jobs = self._list(grid, "Active Jobs", 1, 0, None)
        self.models = self._list(grid, "Models", 1, 1, lambda _i: state.navigate.emit("models"))
        self.root.addLayout(grid, 1)

        JobBridge.instance().job_changed.connect(lambda _job: self._refresh_jobs() if self.isVisible() else None)
        state.data_changed.connect(lambda _what: self.refresh() if self.isVisible() else None)

    def _list(self, grid, title, row, col, on_activate):
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        widget = QListWidget()
        if on_activate:
            widget.itemActivated.connect(on_activate)
        layout.addWidget(widget)
        grid.addWidget(box, row, col)
        return widget

    def _fill(self, widget: QListWidget, rows: list[tuple[str, object]], empty: str):
        widget.clear()
        for text, data in rows or [(empty, None)]:
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, data)
            widget.addItem(item)

    def refresh(self):
        self.run(self._load, self._show, busy=False)

    def _load(self):
        return {
            "projects": project_service.list_projects(limit=8),
            "voices": voice_service.list_voices()[:8],
            "audio": audio_service.list_audios(limit=8),
            "models": model_service.list_models(speaking_only=True),
        }

    def _show(self, data):
        self._fill(self.projects, [(f"{p['name']}  · {p['project_type']}", p["projects_id"])
                                   for p in data["projects"]], "No projects yet")
        self._fill(self.voices, [(f"{v['name']}  · {v['sample_count']} sample(s)", v["voices_id"])
                                 for v in data["voices"]], "No voices yet — clone one")
        self._fill(self.audio, [(f"{a['name']}  · {format_duration(a['duration'])}", a["audios_id"])
                                for a in data["audio"]], "No audio yet")
        self._fill(self.models, [(f"{m['name']}  · {self._model_state(m)}", m["key"]) for m in data["models"]],
                   "No models")
        local_ready = any(m["installed"] and not m["online"] for m in data["models"])
        self.banner.setVisible(not local_ready)
        self.banner.setText(
            "No local speech model is installed yet. Open Models and install Piper (runs offline on CPU), "
            "or enable online engines in Settings."
        )
        self._refresh_jobs()

    @staticmethod
    def _model_state(model: dict) -> str:
        if model["loaded"]:
            return "loaded"
        if model["online"] and not model["allowed"]:
            return "online, disabled in Settings"
        return model["install_label"]

    def _refresh_jobs(self):
        active = job_service.list_jobs(active_only=True)
        self._fill(self.jobs, [(f"{j['title']}  · {j['status_label']} {j['progress'] * 100:.0f}%", j["jobs_id"])
                               for j in active], "Nothing running")

    def _open_project(self, item):
        if item.data(Qt.UserRole) is not None:
            self.state.set_project(item.data(Qt.UserRole))
            self.state.navigate.emit("studio")

    def _open_audio(self, item):
        if item.data(Qt.UserRole) is not None:
            self.state.open_audio.emit(item.data(Qt.UserRole))
