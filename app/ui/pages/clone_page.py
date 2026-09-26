"""Clone Voice: Select sample → Analysis → Consent → Voice settings → Clone → Preview → Save."""

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtMultimedia import QAudioInput, QMediaCaptureSession, QMediaDevices, QMediaFormat, QMediaRecorder
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.constants.models import ModelType
from app.services.clone_service import PREVIEW_TEXT, clone_service
from app.services.consent_service import consent_service
from app.services.system_service import system_service
from app.services.voice_service import voice_service
from app.ui.pages import BasePage
from app.ui.widgets.audio_player import AudioPlayer
from app.ui.widgets.model_selector import ModelSelector
from app.utils.files import subdir, unique_path

AUDIO_FILTER = "Audio files (*.wav *.mp3 *.flac *.ogg *.m4a *.aac *.opus)"


class ClonePage(BasePage):
    title = "Clone Voice"
    subtitle = "Add or record clean samples, confirm the speaker's consent, then clone."

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.samples: list[dict] = []  # {"path", "analysis"}
        self.voice: dict | None = None

        content = QWidget()
        layout = QVBoxLayout(content)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        self.root.addWidget(scroll, 1)

        # 1. Samples
        step1 = QGroupBox("1 · Select samples (3 s – 5 min of clean speech, one speaker)")
        s1 = QVBoxLayout(step1)
        buttons = QHBoxLayout()
        add = QPushButton("Add audio files…")
        add.clicked.connect(self.add_files)
        self.record_button = QPushButton("Record sample")
        self.record_button.clicked.connect(self.toggle_record)
        remove = QPushButton("Remove selected")
        remove.clicked.connect(self.remove_selected)
        buttons.addWidget(add)
        buttons.addWidget(self.record_button)
        buttons.addWidget(remove)
        buttons.addStretch()
        s1.addLayout(buttons)

        # 2. Analysis
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["Sample", "Duration", "Sample rate", "Loudness", "SNR", "Quality",
                                              "Issues"])
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self.table.setMinimumHeight(140)
        step2 = QGroupBox("2 · Audio analysis")
        s2 = QVBoxLayout(step2)
        s2.addWidget(self.table)
        self.total_label = QLabel("No samples yet")
        s2.addWidget(self.total_label)

        # 3. Consent
        step3 = QGroupBox("3 · Consent (required)")
        s3 = QFormLayout(step3)
        self.speaker = QLineEdit()
        self.speaker.setPlaceholderText("Name of the person whose voice this is")
        self.granted_by = QLineEdit()
        self.granted_by.setPlaceholderText("Who is granting consent (the speaker or their authorised representative)")
        self.statement = QPlainTextEdit()
        self.statement.setMaximumHeight(80)
        self.statement.setReadOnly(True)
        self.confirm = QCheckBox("I confirm this statement is true and the speaker has explicitly agreed.")
        self.speaker.textChanged.connect(self._update_statement)
        self.confirm.toggled.connect(self._update_buttons)
        self.granted_by.textChanged.connect(self._update_buttons)
        s3.addRow("Speaker", self.speaker)
        s3.addRow("Granted by", self.granted_by)
        s3.addRow("Statement", self.statement)
        s3.addRow("", self.confirm)

        # 4. Voice settings
        step4 = QGroupBox("4 · Voice settings")
        s4 = QFormLayout(step4)
        self.name = QLineEdit()
        self.language = QLineEdit("en")
        self.description = QLineEdit()
        self.model = ModelSelector(model_types=(ModelType.CLONE, ModelType.EMBED), default_label="",
                                   speaking_only=False)
        s4.addRow("Voice name", self.name)
        s4.addRow("Language", self.language)
        s4.addRow("Description", self.description)
        s4.addRow("Cloning model", self.model)
        self.model_hint = QLabel(
            "Real cloning needs XTTS, F5-TTS or Chatterbox (Models page). The built-in voice profile works "
            "offline with any speech model and matches the speaker's pitch."
        )
        self.model_hint.setObjectName("Hint")
        self.model_hint.setWordWrap(True)
        s4.addRow("", self.model_hint)

        # 5. Clone / preview / save
        step5 = QGroupBox("5 · Clone, preview and save")
        s5 = QVBoxLayout(step5)
        row = QHBoxLayout()
        self.clone_button = QPushButton("Clone voice")
        self.clone_button.setObjectName("Primary")
        self.clone_button.clicked.connect(self.clone)
        self.preview_button = QPushButton("Preview")
        self.preview_button.clicked.connect(self.preview)
        self.save_button = QPushButton("Save && open Voices")
        self.save_button.clicked.connect(self.save)
        for button in (self.clone_button, self.preview_button, self.save_button):
            row.addWidget(button)
        row.addStretch()
        s5.addLayout(row)
        self.preview_text = QLineEdit(PREVIEW_TEXT)
        s5.addWidget(self.preview_text)
        self.player = AudioPlayer()
        s5.addWidget(self.player)
        self.result_label = QLabel("")
        s5.addWidget(self.result_label)

        for box in (step1, step2, step3, step4, step5):
            layout.addWidget(box)
        layout.addStretch()

        self._recorder = None
        self._update_statement()
        self.refresh()

    # ------------------------------------------------------------ samples

    def add_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Choose voice samples", "", AUDIO_FILTER)
        for path in paths:
            self._add_sample(path)

    def _add_sample(self, path: str):
        entry = {"path": path, "analysis": None}
        self.samples.append(entry)
        if not self.name.text():
            self.name.setText(Path(path).stem.replace("_", " ").title())
        self._render_table()
        self.run(lambda: clone_service.analyze_sample(path), lambda a: self._set_analysis(entry, a))

    def _set_analysis(self, entry, analysis):
        entry["analysis"] = analysis
        self._render_table()

    def remove_selected(self):
        rows = sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.samples.pop(row)
        self._render_table()

    def _render_table(self):
        self.table.setRowCount(len(self.samples))
        total = 0.0
        for row, sample in enumerate(self.samples):
            a = sample["analysis"]
            if a:
                total += a["duration"]
                values = [Path(sample["path"]).name, f"{a['duration']:.1f} s", f"{a['sample_rate']} Hz",
                          f"{a['loudness_lufs']:.1f} LUFS", f"{a['snr_db']:.0f} dB", f"{a['quality_score']}/100",
                          "; ".join(a["errors"] + a["issues"]) or "Good"]
            else:
                values = [Path(sample["path"]).name, "analyzing…", "", "", "", "", ""]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                if a and a["errors"] and col == 6:
                    item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()
        self.total_label.setText(f"{len(self.samples)} sample(s), {total:.1f} s total" if self.samples
                                 else "No samples yet")
        self._update_buttons()

    # ------------------------------------------------------------ recording

    def toggle_record(self):
        if self._recorder is not None and self._recorder.recorderState() == QMediaRecorder.RecorderState.RecordingState:
            self._recorder.stop()
            return
        path = unique_path(subdir("cache", "recordings"), "recording", "wav")
        session = QMediaCaptureSession(self)
        wanted = system_service.get_setting("input_device")
        device = next((d for d in QMediaDevices.audioInputs() if d.description() == wanted),
                      QMediaDevices.defaultAudioInput())
        if device.isNull():
            self.error("No microphone found")
            return
        session.setAudioInput(QAudioInput(device, self))
        recorder = QMediaRecorder(self)
        media_format = QMediaFormat(QMediaFormat.FileFormat.Wave)
        recorder.setMediaFormat(media_format)
        recorder.setQuality(QMediaRecorder.Quality.HighQuality)
        recorder.setOutputLocation(QUrl.fromLocalFile(str(path)))
        session.setRecorder(recorder)
        recorder.recorderStateChanged.connect(lambda s: self._on_record_state(s, recorder))
        recorder.errorOccurred.connect(lambda _e, msg: self.error(f"Recording failed: {msg}"))
        self._session, self._recorder = session, recorder
        recorder.record()

    def _on_record_state(self, state, recorder):
        recording = state == QMediaRecorder.RecorderState.RecordingState
        self.record_button.setText("Stop recording" if recording else "Record sample")
        if state == QMediaRecorder.RecorderState.StoppedState:
            location = recorder.actualLocation().toLocalFile()
            if location and Path(location).exists():
                self._add_sample(location)

    # ------------------------------------------------------------ consent

    def _update_statement(self):
        self.statement.setPlainText(consent_service.statement_for(self.speaker.text().strip()))
        self._update_buttons()

    def _consent(self) -> dict:
        return {"confirmed": self.confirm.isChecked(), "granted_by": self.granted_by.text(),
                "speaker_name": self.speaker.text(), "statement": self.statement.toPlainText()}

    def _update_buttons(self):
        ready = (bool(self.samples) and all(s["analysis"] and s["analysis"]["ok"] for s in self.samples)
                 and self.confirm.isChecked() and bool(self.granted_by.text().strip())
                 and bool(self.speaker.text().strip()))
        self.clone_button.setEnabled(ready and self.voice is None)
        self.preview_button.setEnabled(self.voice is not None)
        self.save_button.setEnabled(self.voice is not None)

    # ------------------------------------------------------------ clone / preview / save

    def clone(self):
        try:
            job = clone_service.clone_async(
                [s["path"] for s in self.samples], self.name.text(), self._consent(),
                language=self.language.text().strip() or "en", description=self.description.text(),
                model_key=self.model.model_key(),
            )
        except Exception as exc:
            self.error(exc)
            return
        self.clone_button.setEnabled(False)
        self.follow(job, self._cloned)

    def _cloned(self, result):
        voice = self.voice = result["voice"]
        self.result_label.setText(f"Voice “{voice['name']}” created with {voice['sample_count']} sample(s). "
                                  "Preview it, then save.")
        self.state.notify("voices")
        self._update_buttons()

    def preview(self):
        if not self.voice:
            return
        job = clone_service.preview_async(self.voice["voices_id"], self.preview_text.text())
        self.follow(job, lambda r: (self.player.load(r["audio"]["path"], "Preview"), self.player.play()))

    def save(self):
        if not self.voice:
            return
        voices_id, name, description = self.voice["voices_id"], self.name.text(), self.description.text()
        self.run(lambda: voice_service.update(voices_id, name=name, description=description), self._saved)

    def _saved(self, _voice):
        self.state.notify("voices")
        self.reset()
        self.state.navigate.emit("voices")

    def reset(self):
        self.samples.clear()
        self.voice = None
        self.player.load(None)
        self.confirm.setChecked(False)
        self.result_label.setText("")
        self.name.clear()
        self.description.clear()
        self._render_table()

    def refresh(self):
        self.model.refresh(preferred=system_service.get_setting("default_clone_model"))
