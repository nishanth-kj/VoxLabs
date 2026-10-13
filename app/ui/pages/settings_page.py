"""Settings: appearance, devices, defaults, export, GPU and performance, the optional REST API and the log level.

The logs themselves are in the bottom Logs panel (View → Logs Panel).
"""

from PySide6.QtCore import Qt
from PySide6.QtMultimedia import QMediaDevices
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.constants.audio import ENHANCE_PRESETS, EXPORT_FORMATS, SAMPLE_RATES
from app.constants.models import ModelType
from app.constants.performance import (
    BATCH_SIZE_MAX,
    JOB_WORKERS_MAX,
    PERFORMANCE_PRESET_LABELS,
    PERFORMANCE_PRESETS,
)
from app.services.model_service import model_service
from app.services.system_service import system_service
from app.ui.pages import BasePage
from app.ui.widgets.model_selector import ModelSelector
from app.ui.widgets.voice_selector import VoiceSelector
from app.utils import device
from app.ui.widgets.select import Select


class SettingsPage(BasePage):
    title = "Settings"
    subtitle = "Appearance, audio devices, defaults and the local API."

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        column = QVBoxLayout()

        appearance = QGroupBox("Appearance")
        appearance_form = QFormLayout(appearance)
        self.theme = Select()
        for mode, label in (("system", "Match system"), ("dark", "Dark"), ("light", "Light")):
            self.theme.addItem(label, mode)
        self.native_title_bar = QCheckBox("Use the system title bar (applies after restart)")
        appearance_form.addRow("Theme", self.theme)
        appearance_form.addRow("", self.native_title_bar)
        column.addWidget(appearance)

        audio = QGroupBox("Audio")
        audio_form = QFormLayout(audio)
        self.output_device = Select()
        self.input_device = Select()
        self.export_format = Select()
        self.export_format.addItems(list(EXPORT_FORMATS))
        self.sample_rate = Select()
        for rate in SAMPLE_RATES:
            self.sample_rate.addItem(f"{rate} Hz", rate)
        self.output_dir = QLineEdit()
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse)
        out_row = QHBoxLayout()
        out_row.addWidget(self.output_dir)
        out_row.addWidget(browse)
        out_widget = QWidget()
        out_widget.setLayout(out_row)
        self.enhance_preset = Select()
        self.enhance_preset.addItems(list(ENHANCE_PRESETS))
        audio_form.addRow("Output device", self.output_device)
        audio_form.addRow("Input device", self.input_device)
        audio_form.addRow("Default export format", self.export_format)
        audio_form.addRow("Default sample rate", self.sample_rate)
        audio_form.addRow("Default output folder", out_widget)
        audio_form.addRow("Default enhancement", self.enhance_preset)
        column.addWidget(audio)

        voice = QGroupBox("Voices and models")
        voice_form = QFormLayout(voice)
        self.default_voice = VoiceSelector()
        self.default_tts = ModelSelector(default_label="", only_usable=False)
        self.default_clone = ModelSelector(model_types=(ModelType.CLONE, ModelType.EMBED), default_label="",
                                           speaking_only=False, only_usable=False)
        self.allow_online = QCheckBox("Allow online engines (sends text to Google / Microsoft)")
        self.allow_edge = QCheckBox("Microsoft Edge voices")
        self.allow_edge.setToolTip("Off hides every Microsoft Edge voice. Turn this on to use them.")
        self.device = Select()
        voice_form.addRow("Default voice", self.default_voice)
        voice_form.addRow("Default speech model", self.default_tts)
        voice_form.addRow("Default cloning model", self.default_clone)
        voice_form.addRow("GPU / device", self.device)
        voice_form.addRow("", self.allow_online)
        voice_form.addRow("", self.allow_edge)
        column.addWidget(voice)
        column.addWidget(self._performance_group())

        api = QGroupBox("REST API (optional)")
        api_form = QFormLayout(api)
        self.api_enabled = QCheckBox("Start the local API with VoxLabs")
        self.api_host = QLineEdit()
        self.api_port = QSpinBox()
        self.api_port.setRange(1, 65535)
        self.api_token = QLineEdit()
        self.api_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_token.setPlaceholderText("Required when the host is not 127.0.0.1")
        self.api_status = QLabel("")
        self.api_status.setObjectName("Hint")
        api_form.addRow("", self.api_enabled)
        api_form.addRow("Host", self.api_host)
        api_form.addRow("Port", self.api_port)
        api_form.addRow("Token", self.api_token)
        api_form.addRow("", self.api_status)
        column.addWidget(api)

        general = QGroupBox("General")
        general_form = QFormLayout(general)
        self.autosave = QCheckBox("Autosave editor state")
        self.log_level = Select()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        logs_hint = QLabel("Logs are in the bottom panel: View → Logs Panel (Ctrl+`).")
        logs_hint.setObjectName("Hint")
        logs_hint.setWordWrap(True)
        general_form.addRow("", self.autosave)
        general_form.addRow("Log level", self.log_level)
        general_form.addRow("", logs_hint)
        column.addWidget(general)
        column.addStretch(1)

        # Scroll instead of squeezing the forms on short windows.
        content = QWidget()
        content.setLayout(column)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(content)
        self.root.addWidget(scroll, 1)
        state.data_changed.connect(lambda what: self._theme_saved() if what == "settings" else None)
        save = QPushButton("Save settings")
        save.setObjectName("Primary")
        save.clicked.connect(self.save)
        self.root.addWidget(save)

    def _performance_group(self) -> QGroupBox:
        """Speed versus memory: a preset fills in the values below, which stay editable."""
        self._filling = True  # no "edited" reactions while the widgets are being built
        box = QGroupBox("Performance")
        form = QFormLayout(box)
        self.hardware = QLabel("Checking this computer…")
        self.hardware.setObjectName("Hint")
        self.hardware.setWordWrap(True)
        self.performance_preset = Select()
        for key, label in PERFORMANCE_PRESET_LABELS.items():
            self.performance_preset.addItem(label, key)
        self.performance_preset.addItem("Custom", "custom")
        self.performance_preset.currentIndexChanged.connect(self._apply_performance_preset)
        self.max_loaded_models = self._spin(0, 16, "No limit")
        self.max_loaded_models.setToolTip("Models kept in memory at once; the least recently used is unloaded first. "
                                          "Models on the GPU also make room for each other when VRAM runs out.")
        self.gpu_memory_budget = self._spin(0, 1 << 20, "All free VRAM", " MB", 256)
        self.gpu_memory_reserve = self._spin(0, 1 << 16, "None", " MB", 256)
        self.gpu_memory_reserve.setToolTip("VRAM left free for other programs when deciding whether a model fits.")
        self.precision = Select()
        for key, label in (("auto", "Engine default"), ("full", "Full (float32)"),
                           ("half", "Half where supported (float16/bfloat16)")):
            self.precision.addItem(label, key)
        self.batch_size = self._spin(1, BATCH_SIZE_MAX)
        self.batch_size.setToolTip("Text chunks sent to an engine in one call, for engines that batch (Qwen3-TTS).")
        self.job_workers = self._spin(1, JOB_WORKERS_MAX)
        self.preload_default_model = QCheckBox("Load the default speech model when VoxLabs starts")
        self.release_memory_after_job = QCheckBox("Hand GPU memory back after every job")
        self.loaded_models = QLabel("")
        self.loaded_models.setObjectName("Hint")
        self.loaded_models.setWordWrap(True)
        unload = QPushButton("Unload all models")
        unload.clicked.connect(lambda: self.run(model_service.unload_all, lambda _r: (
            self.state.notify("models"), self._refresh_performance())))
        loaded_row = QHBoxLayout()
        loaded_row.addWidget(self.loaded_models, 1)
        loaded_row.addWidget(unload)
        form.addRow("", self.hardware)
        form.addRow("Preset", self.performance_preset)
        form.addRow("Models kept loaded", self.max_loaded_models)
        form.addRow("GPU memory budget", self.gpu_memory_budget)
        form.addRow("VRAM left for other apps", self.gpu_memory_reserve)
        form.addRow("Precision", self.precision)
        form.addRow("Batch size", self.batch_size)
        form.addRow("Jobs at the same time", self.job_workers)
        form.addRow("", self.preload_default_model)
        form.addRow("", self.release_memory_after_job)
        form.addRow("In memory", loaded_row)
        for widget in (self.max_loaded_models, self.gpu_memory_budget, self.gpu_memory_reserve, self.batch_size,
                       self.job_workers):
            widget.valueChanged.connect(self._performance_edited)
        self.precision.currentIndexChanged.connect(self._performance_edited)
        for box_ in (self.preload_default_model, self.release_memory_after_job):
            box_.toggled.connect(self._performance_edited)
        self._filling = False
        return box

    @staticmethod
    def _spin(low: int, high: int, special: str = "", suffix: str = "", step: int = 1) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(low, high)
        spin.setSingleStep(step)
        if special:
            spin.setSpecialValueText(special)
        if suffix:
            spin.setSuffix(suffix)
        return spin

    def _performance_values(self) -> dict:
        return {
            "max_loaded_models": self.max_loaded_models.value(),
            "gpu_memory_budget_mb": self.gpu_memory_budget.value(),
            "gpu_memory_reserve_mb": self.gpu_memory_reserve.value(),
            "precision": self.precision.currentData() or "auto",
            "batch_size": self.batch_size.value(),
            "job_workers": self.job_workers.value(),
            "preload_default_model": self.preload_default_model.isChecked(),
            "release_memory_after_job": self.release_memory_after_job.isChecked(),
        }

    def _fill_performance(self, values: dict) -> None:
        self._filling = True
        self.max_loaded_models.setValue(int(values["max_loaded_models"]))
        self.gpu_memory_budget.setValue(int(values["gpu_memory_budget_mb"]))
        self.gpu_memory_reserve.setValue(int(values["gpu_memory_reserve_mb"]))
        self._select(self.precision, values["precision"])
        self.batch_size.setValue(int(values["batch_size"]))
        self.job_workers.setValue(int(values["job_workers"]))
        self.preload_default_model.setChecked(bool(values["preload_default_model"]))
        self.release_memory_after_job.setChecked(bool(values["release_memory_after_job"]))
        self._filling = False

    def _apply_performance_preset(self):
        preset = self.performance_preset.currentData()
        if preset in PERFORMANCE_PRESETS and not self._filling:
            self._fill_performance(PERFORMANCE_PRESETS[preset])

    def _performance_edited(self):
        """A value edited by hand: the preset becomes Custom unless the values still match one exactly."""
        if self._filling:
            return
        values = self._performance_values()
        match = next((key for key, preset in PERFORMANCE_PRESETS.items() if preset == values), "custom")
        self._filling = True
        self._select(self.performance_preset, match)
        self._filling = False

    def _refresh_performance(self):
        def load():
            hardware = system_service.devices()
            return hardware, model_service.loaded_models()

        def show(data):
            hardware, loaded = data
            gpus = ", ".join(f"{g['name']} ({g['vram_total_mb'] / 1024:.1f} GB, {g['vram_free_mb'] / 1024:.1f} GB free)"
                             for g in hardware["gpus"]) or "none"
            cuda = "CUDA ready" if hardware["cuda"] else ("no CUDA build of torch" if hardware["gpus"] else "")
            ram = hardware["ram_mb"]
            memory = f"RAM {ram['total'] / 1024:.1f} GB ({ram['available'] / 1024:.1f} GB free)" if ram["total"] else ""
            recommended = PERFORMANCE_PRESET_LABELS[hardware["recommended_preset"]]
            self.hardware.setText(" · ".join(part for part in (f"GPU: {gpus}", cuda, memory) if part)
                                  + f"\nRecommended for this computer: {recommended}")
            self.loaded_models.setText(", ".join(f"{m['key']} ({m['device']})" for m in loaded) or "No models loaded")

        self.run(load, show, busy=False)

    def _browse(self):
        folder = QFileDialog.getExistingDirectory(self, "Default output folder", self.output_dir.text())
        if folder:
            self.output_dir.setText(folder)

    def refresh(self):
        s = system_service.get_settings()
        self.output_device.clear()
        self.output_device.addItem("System default", "")
        for dev in QMediaDevices.audioOutputs():
            self.output_device.addItem(dev.description(), dev.description())
        self.input_device.clear()
        self.input_device.addItem("System default", "")
        for dev in QMediaDevices.audioInputs():
            self.input_device.addItem(dev.description(), dev.description())
        self._select(self.output_device, s["output_device"])
        self._select(self.input_device, s["input_device"])
        self.export_format.setCurrentText(s["export_format"])
        self._select(self.sample_rate, s["sample_rate"])
        self.output_dir.setText(s["output_dir"])
        self.enhance_preset.setCurrentText(s["enhance_preset"])
        self.default_voice.refresh()
        self.default_voice.set_voices_id(s["default_voices_id"])
        self.default_tts.refresh()
        self.default_tts.set_model_key(s["default_tts_model"])
        self.default_clone.refresh()
        self.default_clone.set_model_key(s["default_clone_model"])
        self.device.clear()
        self.device.addItem("Automatic", "auto")
        for name in device.available_devices():
            self.device.addItem(name, name)
        self._select(self.device, s["device"])
        self.allow_online.setChecked(bool(s["allow_online_models"]))
        self.allow_edge.setChecked(bool(s.get("allow_edge")))
        self.api_enabled.setChecked(bool(s["api_enabled"]))
        self.api_host.setText(s["api_host"])
        self.api_port.setValue(int(s["api_port"]))
        self.api_token.setText(s["api_token"])
        self.autosave.setChecked(bool(s["autosave"]))
        self.log_level.setCurrentText(s["log_level"])
        self._filling = True
        self._select(self.performance_preset, s["performance_preset"])
        self._filling = False
        self._fill_performance(s)
        self._refresh_performance()
        self._select(self.theme, s["theme"])
        self.native_title_bar.setChecked(bool(s["native_title_bar"]))
        running = system_service.api_running()
        self.api_status.setText(f"Running at http://{s['api_host']}:{s['api_port']}/docs" if running
                                else "Not running")

    def _theme_saved(self):
        """The theme was switched elsewhere (View → Theme): show it without touching unsaved edits."""
        self._select(self.theme, system_service.get_setting("theme"))

    def _select(self, combo: QComboBox, value):
        index = combo.findData(value)
        combo.setCurrentIndex(max(index, 0))

    def save(self):
        changes = {
            "output_device": self.output_device.currentData() or "",
            "input_device": self.input_device.currentData() or "",
            "export_format": self.export_format.currentText(),
            "sample_rate": self.sample_rate.currentData(),
            "output_dir": self.output_dir.text().strip(),
            "enhance_preset": self.enhance_preset.currentText(),
            "default_voices_id": self.default_voice.voices_id(),
            "default_tts_model": self.default_tts.model_key() or system_service.get_setting("default_tts_model"),
            "default_clone_model": self.default_clone.model_key() or system_service.get_setting("default_clone_model"),
            "device": self.device.currentData() or "auto",
            "allow_online_models": self.allow_online.isChecked(),
            "allow_edge": self.allow_edge.isChecked(),
            "api_enabled": self.api_enabled.isChecked(),
            "api_host": self.api_host.text().strip() or "127.0.0.1",
            "api_port": self.api_port.value(),
            "api_token": self.api_token.text().strip(),
            "autosave": self.autosave.isChecked(),
            "log_level": self.log_level.currentText(),
            "theme": self.theme.currentData() or "system",
            "native_title_bar": self.native_title_bar.isChecked(),
            "performance_preset": self.performance_preset.currentData() or "custom",
            **self._performance_values(),
        }

        def apply():
            reload = changes["precision"] != system_service.get_setting("precision")
            settings = system_service.update_settings(**changes)
            if reload:  # loaded models keep the precision they were loaded with
                model_service.unload_all()
            system_service.apply_api_setting()
            return settings

        self.run(apply, lambda _s: (self.state.notify("settings"), self.state.notify("models"), self.refresh()))
