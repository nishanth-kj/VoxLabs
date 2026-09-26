"""Models: install, load, unload, remove, reload, health check and default selection."""

from PySide6.QtWidgets import QHBoxLayout, QHeaderView, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem

from app.constants.models import Backend, ModelType
from app.services.model_service import model_service
from app.services.system_service import system_service
from app.ui.pages import BasePage

COLUMNS = ("Model", "Type", "Size", "Status", "Loaded / device", "VRAM", "Capabilities", "Runs")


class ModelsPage(BasePage):
    title = "Models"
    subtitle = "Install, load and choose speech and cloning engines."

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.models: list[dict] = []
        self.devices = QLabel("")
        self.devices.setObjectName("Hint")
        self.root.addWidget(self.devices)
        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        for label, slot in (("Install", self.install), ("Load", self.load), ("Unload", self.unload),
                            ("Reload", self.reload), ("Remove", self.remove), ("Health check", self.health),
                            ("Set as default", self.set_default), ("Rescan", self.rescan)):
            button = QPushButton(label)
            button.clicked.connect(slot)
            actions.addWidget(button)
        actions.addStretch()
        self.root.addLayout(actions)
        hint = QLabel("Online engines (Google, Microsoft Edge) send text to a third party and are disabled unless "
                      "enabled in Settings. Heavy engines need their Python extra, e.g. `uv sync --extra xtts`.")
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        self.root.addWidget(hint)

    def refresh(self):
        self.run(lambda: (model_service.list_models(), system_service.devices()), self._show, busy=False)

    def _show(self, data):
        self.models, devices = data
        gpus = ", ".join(f"{g['name']} ({g['vram_free_mb']} / {g['vram_total_mb']} MB free)" for g in devices["gpus"])
        cuda = "CUDA ready" if devices["cuda"] else ("GPU found; install a CUDA build of torch to use it"
                                                   if devices["gpus"] else "no CUDA GPU")
        self.devices.setText(f"CPU: {devices['cpu']['name']} · {devices['cpu']['cores']} cores   |   "
                             f"GPU: {gpus or 'none'} · {cuda}")
        defaults = {system_service.get_setting("default_tts_model"), system_service.get_setting("default_clone_model")}
        self.table.setRowCount(len(self.models))
        for row, model in enumerate(self.models):
            loaded = f"Loaded on {model['loaded_device']}" if model["loaded"] else "—"
            if not model["speaks"]:
                loaded = "built in"
            values = (
                model["name"] + ("  ★ default" if model["key"] in defaults else ""),
                model["model_type"].upper(),
                f"{model['size_mb']} MB" if model["size_mb"] else "—",
                model["install_label"] if model["package_installed"] else f"needs `--extra {model['extra']}`",
                loaded,
                f"{model['vram_mb']} MB" if model["vram_mb"] else "CPU ok",
                ", ".join(model["capabilities"]),
                ("online" + ("" if model["allowed"] else " (disabled)")) if model["online"] else "local",
            )
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

    def _current(self):
        row = self.table.currentRow()
        if 0 <= row < len(self.models):
            return self.models[row]
        self.error("Select a model first")
        return None

    def _changed(self, _result=None):
        self.state.notify("models")
        self.refresh()

    def install(self):
        model = self._current()
        if not model:
            return
        accept = False
        if model["backend"] == Backend.XTTS:
            accept = QMessageBox.question(
                self, "Coqui Public Model License",
                "XTTS v2 is licensed under the Coqui Public Model License (non-commercial use only). "
                "Do you accept the license and want to download the model (~1.9 GB)?") == QMessageBox.StandardButton.Yes
            if not accept:
                return
        try:
            job = model_service.install_async(model["key"], accept_license=accept)
        except Exception as exc:
            self.error(exc)
            return
        self.follow(job, self._changed)

    def load(self):
        model = self._current()
        if model:
            self.follow(model_service.load_async(model["key"]), self._changed)

    def unload(self):
        model = self._current()
        if model:
            self.run(lambda: model_service.unload(model["key"]), self._changed)

    def reload(self):
        model = self._current()
        if model:
            self.run(lambda: model_service.reload(model["key"]), self._changed)

    def remove(self):
        model = self._current()
        if model and QMessageBox.question(self, "Remove model",
                                          f"Remove downloaded files for {model['name']}?") == QMessageBox.StandardButton.Yes:
            self.run(lambda: model_service.remove(model["key"]), self._changed)

    def health(self):
        model = self._current()
        if model:
            self.run(lambda: model_service.health(model["key"]), lambda h: QMessageBox.information(
                self, "Health check", f"{model['name']}: " + ("OK" if h["ok"] else "\n".join(h["problems"]))))

    def set_default(self):
        model = self._current()
        if not model:
            return
        kinds = [ModelType.CLONE if model["model_type"] in (ModelType.CLONE, ModelType.EMBED) else ModelType.TTS]
        if model["model_type"] == ModelType.CLONE and model["speaks"] and QMessageBox.question(
                self, "Set default", "Use it as the default speech model too?") == QMessageBox.StandardButton.Yes:
            kinds.append(ModelType.TTS)
        self.run(lambda: [model_service.select(kind, model["key"]) for kind in kinds], self._changed)

    def rescan(self):
        self.run(model_service.discover, lambda _m: self._changed())
