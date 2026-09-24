"""Settings: devices, defaults, export, GPU, optional REST API and logging."""

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
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from app.constants.audio import ENHANCE_PRESETS, EXPORT_FORMATS, SAMPLE_RATES
from app.constants.models import ModelType
from app.services.system_service import system_service
from app.ui.pages import BasePage
from app.ui.widgets.model_selector import ModelSelector
from app.ui.widgets.voice_selector import VoiceSelector
from app.utils import device


class SettingsPage(BasePage):
    title = "Settings"

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        columns = QHBoxLayout()
        left, right = QFormLayout(), QFormLayout()

        audio = QGroupBox("Audio")
        audio_form = QFormLayout(audio)
        self.output_device = QComboBox()
        self.input_device = QComboBox()
        self.export_format = QComboBox()
        self.export_format.addItems(list(EXPORT_FORMATS))
        self.sample_rate = QComboBox()
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
        self.enhance_preset = QComboBox()
        self.enhance_preset.addItems(list(ENHANCE_PRESETS))
        audio_form.addRow("Output device", self.output_device)
        audio_form.addRow("Input device", self.input_device)
        audio_form.addRow("Default export format", self.export_format)
        audio_form.addRow("Default sample rate", self.sample_rate)
        audio_form.addRow("Default output folder", out_widget)
        audio_form.addRow("Default enhancement", self.enhance_preset)
        left.addRow(audio)

        voice = QGroupBox("Voices and models")
        voice_form = QFormLayout(voice)
        self.default_voice = VoiceSelector()
        self.default_tts = ModelSelector(default_label="", only_usable=False)
        self.default_clone = ModelSelector(model_types=(ModelType.CLONE, ModelType.EMBED), default_label="",
                                           speaking_only=False, only_usable=False)
        self.allow_online = QCheckBox("Allow online engines (sends text to Google / Microsoft)")
        self.device = QComboBox()
        voice_form.addRow("Default voice", self.default_voice)
        voice_form.addRow("Default speech model", self.default_tts)
        voice_form.addRow("Default cloning model", self.default_clone)
        voice_form.addRow("GPU / device", self.device)
        voice_form.addRow("", self.allow_online)
        left.addRow(voice)

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
        right.addRow(api)

        general = QGroupBox("General")
        general_form = QFormLayout(general)
        self.autosave = QCheckBox("Autosave editor state")
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        general_form.addRow("", self.autosave)
        general_form.addRow("Log level", self.log_level)
        self.logs = QPlainTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setMinimumHeight(160)
        refresh_logs = QPushButton("Refresh logs")
        refresh_logs.clicked.connect(self._show_logs)
        general_form.addRow(self.logs)
        general_form.addRow(refresh_logs)
        right.addRow(general)

        columns.addLayout(left, 1)
        columns.addLayout(right, 1)
        self.root.addLayout(columns, 1)
        save = QPushButton("Save settings")
        save.clicked.connect(self.save)
        self.root.addWidget(save)

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
        self.api_enabled.setChecked(bool(s["api_enabled"]))
        self.api_host.setText(s["api_host"])
        self.api_port.setValue(int(s["api_port"]))
        self.api_token.setText(s["api_token"])
        self.autosave.setChecked(bool(s["autosave"]))
        self.log_level.setCurrentText(s["log_level"])
        running = system_service.api_running()
        self.api_status.setText(f"Running at http://{s['api_host']}:{s['api_port']}/docs" if running
                                else "Not running")
        self._show_logs()

    def _select(self, combo: QComboBox, value):
        index = combo.findData(value)
        combo.setCurrentIndex(max(index, 0))

    def _show_logs(self):
        lines = [f"{e['ts'][11:19]}  {e['level'].upper():7} {e['message']}" for e in system_service.logs(300)]
        self.logs.setPlainText("\n".join(lines))
        self.logs.verticalScrollBar().setValue(self.logs.verticalScrollBar().maximum())

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
            "api_enabled": self.api_enabled.isChecked(),
            "api_host": self.api_host.text().strip() or "127.0.0.1",
            "api_port": self.api_port.value(),
            "api_token": self.api_token.text().strip(),
            "autosave": self.autosave.isChecked(),
            "log_level": self.log_level.currentText(),
        }

        def apply():
            settings = system_service.update_settings(**changes)
            system_service.apply_api_setting()
            return settings

        self.run(apply, lambda _s: (self.state.notify("settings"), self.state.notify("models"), self.refresh()))
