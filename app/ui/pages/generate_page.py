"""Generate Audio: text → speech with voice/model/prosody controls and per-sentence regeneration."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.constants.audio import EMOTIONS, ENHANCE_PRESETS, EXPORT_FORMATS, PAUSE_SENTENCE_MS, PROCESS_STEPS, STYLES
from app.services.audio_service import audio_service
from app.services.system_service import system_service
from app.services.tts_service import tts_service
from app.ui.pages import BasePage
from app.ui.widgets.audio_player import AudioPlayer
from app.ui.widgets.model_selector import ModelSelector
from app.ui.widgets.voice_selector import VoiceSelector


class GeneratePage(BasePage):
    title = "Generate Audio"

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.sentences: list[dict] = []
        self.combined: dict | None = None

        splitter = QSplitter(Qt.Horizontal)
        self.root.addWidget(splitter, 1)

        # Left: text + results
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(0, 0, 0, 0)
        self.text = QPlainTextEdit()
        self.text.setPlaceholderText("Type or paste text. Use [pause 800ms] or [pause 2s] for manual pauses.")
        lv.addWidget(self.text, 3)
        buttons = QHBoxLayout()
        self.generate_button = QPushButton("Generate")
        self.generate_button.setDefault(True)
        self.generate_button.clicked.connect(self.generate)
        self.sentence_mode = QCheckBox("Per sentence (allows regenerating single sentences)")
        self.sentence_mode.setChecked(True)
        buttons.addWidget(self.generate_button)
        buttons.addWidget(self.sentence_mode)
        buttons.addStretch()
        lv.addLayout(buttons)

        results = QGroupBox("Sentences")
        rv = QVBoxLayout(results)
        self.sentence_list = QListWidget()
        self.sentence_list.itemActivated.connect(self._play_sentence)
        rv.addWidget(self.sentence_list)
        row = QHBoxLayout()
        regen = QPushButton("Regenerate selected sentence")
        regen.clicked.connect(self.regenerate_sentence)
        play = QPushButton("Play sentence")
        play.clicked.connect(lambda: self._play_sentence(self.sentence_list.currentItem()))
        row.addWidget(play)
        row.addWidget(regen)
        row.addStretch()
        rv.addLayout(row)
        lv.addWidget(results, 2)

        self.player = AudioPlayer()
        lv.addWidget(self.player)
        out = QHBoxLayout()
        self.format = QComboBox()
        self.format.addItems(EXPORT_FORMATS)
        export = QPushButton("Export…")
        export.clicked.connect(self.export)
        editor = QPushButton("Open in editor")
        editor.clicked.connect(lambda: self.combined and self.state.open_audio.emit(self.combined["audios_id"]))
        self.save_label = QLabel("")
        out.addWidget(QLabel("Format"))
        out.addWidget(self.format)
        out.addWidget(export)
        out.addWidget(editor)
        out.addStretch()
        out.addWidget(self.save_label)
        lv.addLayout(out)
        splitter.addWidget(left)

        # Right: settings
        right = QWidget()
        form = QFormLayout(right)
        self.voice = VoiceSelector()
        self.model = ModelSelector()
        self.speed = self._spin(0.5, 2.0, 1.0)
        self.pitch = self._spin(0.5, 2.0, 1.0)
        self.energy = self._spin(0.1, 2.0, 1.0)
        self.emotion = QComboBox()
        self.emotion.addItems(list(EMOTIONS))
        self.style_box = QComboBox()
        self.style_box.addItems(list(STYLES))
        self.pause = QSpinBox()
        self.pause.setRange(0, 5000)
        self.pause.setSingleStep(50)
        self.pause.setValue(PAUSE_SENTENCE_MS)
        self.pause.setSuffix(" ms")
        self.temperature = self._spin(0.0, 1.5, 0.0)
        self.temperature.setSpecialValueText("model default")
        self.seed = QSpinBox()
        self.seed.setRange(-1, 2**31 - 1)
        self.seed.setValue(-1)
        self.seed.setSpecialValueText("random")
        self.pronunciations = QPlainTextEdit()
        self.pronunciations.setPlaceholderText("One per line: word = how to say it\nSQL = sequel")
        self.pronunciations.setMaximumHeight(80)
        form.addRow("Voice", self.voice)
        form.addRow("Model", self.model)
        form.addRow("Speed", self.speed)
        form.addRow("Pitch", self.pitch)
        form.addRow("Energy", self.energy)
        form.addRow("Emotion", self.emotion)
        form.addRow("Style", self.style_box)
        form.addRow("Sentence pause", self.pause)
        form.addRow("Temperature", self.temperature)
        form.addRow("Seed", self.seed)
        form.addRow("Pronunciation", self.pronunciations)

        post = QGroupBox("Clean-up (original is always kept)")
        pv = QVBoxLayout(post)
        self.preset = QComboBox()
        self.preset.addItem("Custom steps", None)
        for name in ENHANCE_PRESETS:
            self.preset.addItem(name, name)
        pv.addWidget(self.preset)
        self.steps: dict[str, QCheckBox] = {}
        for step in PROCESS_STEPS:
            box = QCheckBox(step.replace("_", " ").capitalize())
            box.setChecked(step in ("trim_silence", "normalize"))
            self.steps[step] = box
            pv.addWidget(box)
        self.preset.currentIndexChanged.connect(self._apply_preset)
        form.addRow(post)
        splitter.addWidget(right)
        splitter.setSizes([700, 360])

        state.data_changed.connect(self._on_data_changed)

    def _spin(self, low, high, value):
        spin = QDoubleSpinBox()
        spin.setRange(low, high)
        spin.setSingleStep(0.05)
        spin.setValue(value)
        return spin

    def _apply_preset(self):
        preset = self.preset.currentData()
        if preset:
            enabled = ENHANCE_PRESETS[preset]
            for step, box in self.steps.items():
                box.setChecked(step in enabled)

    def _on_data_changed(self, what):
        if what == "voices":
            self.voice.refresh()
        elif what in ("models", "settings"):
            self.model.refresh()

    def refresh(self):
        self.voice.refresh()
        self.model.refresh()
        if self.voice.voices_id() is None:
            self.voice.set_voices_id(system_service.get_setting("default_voices_id"))

    # ------------------------------------------------------------ generation

    def params(self) -> dict:
        pronunciations = {}
        for line in self.pronunciations.toPlainText().splitlines():
            if "=" in line:
                word, spoken = line.split("=", 1)
                pronunciations[word.strip()] = spoken.strip()
        preset = self.preset.currentData()
        if preset is None:  # custom: exactly the ticked steps
            post = {step: {} for step, box in self.steps.items() if box.isChecked()}
        elif preset == "Raw":
            post, preset = {}, None
        else:
            post = None
        return {
            "voices_id": self.voice.voices_id(),
            "model_key": self.model.model_key(),
            "speed": self.speed.value(),
            "pitch": self.pitch.value(),
            "energy": self.energy.value(),
            "emotion": self.emotion.currentText(),
            "style": self.style_box.currentText(),
            "pause_ms": self.pause.value(),
            "pronunciations": pronunciations,
            "temperature": self.temperature.value() or None,
            "seed": None if self.seed.value() < 0 else self.seed.value(),
            "post": post,
            "preset": preset,
            "projects_id": self.state.projects_id,
        }

    def generate(self):
        text = self.text.toPlainText()
        params = self.params()
        try:
            if self.sentence_mode.isChecked():
                job = tts_service.generate_sentences_async(text, gap_ms=params.pop("pause_ms"), **params)
            else:
                job = tts_service.generate_async(text, **params)
        except Exception as exc:
            self.error(exc)
            return
        self.generate_button.setEnabled(False)
        self.follow(job, self._generated, on_fail=lambda: self.generate_button.setEnabled(True))

    def _generated(self, result):
        self.generate_button.setEnabled(True)
        if "sentences" in result:
            self.sentences = result["sentences"]
            self.combined = result["combined"]
        else:
            self.sentences = []
            self.combined = result["audio"]
        self._show_results()
        self.state.notify("audio")

    def _show_results(self):
        self.sentence_list.clear()
        for index, audio in enumerate(self.sentences):
            item = QListWidgetItem(f"{index + 1}. {audio['params'].get('text', '')}")
            item.setData(Qt.UserRole, index)
            self.sentence_list.addItem(item)
        if self.combined:
            self.player.load(self.combined["path"], "Generated speech")
            label = "AI-generated · labeled in file metadata"
            self.save_label.setText(f"{self.combined['duration']:.1f} s · {label}")
            self.player.play()

    def _play_sentence(self, item):
        if item is None:
            return
        audio = self.sentences[item.data(Qt.UserRole)]
        self.player.load(audio["path"], f"Sentence {item.data(Qt.UserRole) + 1}")
        self.player.play()

    def regenerate_sentence(self):
        item = self.sentence_list.currentItem()
        if item is None:
            return
        index = item.data(Qt.UserRole)
        job = tts_service.regenerate_sentence_async([a["audios_id"] for a in self.sentences], index,
                                                    self.pause.value(), self.state.projects_id)
        self.follow(job, lambda r: self._regenerated(index, r))

    def _regenerated(self, index, result):
        self.sentences[index] = result["sentence"]
        self.combined = result["combined"]
        self._show_results()
        self.sentence_list.setCurrentRow(index)

    def export(self):
        if not self.combined:
            return
        fmt = self.format.currentText()
        start_dir = system_service.get_setting("output_dir") or ""
        path, _ = QFileDialog.getSaveFileName(self, "Export audio", f"{start_dir}/speech.{fmt}", f"*.{fmt}")
        if path:
            self.run(lambda: audio_service.export(self.combined["audios_id"], path, fmt),
                     lambda p: self.save_label.setText(f"Saved {p}"))
