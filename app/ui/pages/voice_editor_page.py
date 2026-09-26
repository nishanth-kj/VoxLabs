"""Voice Editor: shape a voice and the model that will speak it later.

Saved delivery (speed, pitch, energy, emotion, style) and the chosen model
are what Generate and script-to-audio use for this voice.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from app.constants.audio import EMOTIONS, STYLES
from app.models.request import TTSRequest
from app.services.tts_service import tts_service
from app.services.voice_service import DELIVERY_DEFAULTS, voice_service
from app.ui.pages import BasePage
from app.ui.widgets.audio_player import AudioPlayer
from app.ui.widgets.model_selector import ModelSelector
from app.ui.widgets.voice_selector import VoiceSelector
from app.utils.time import format_duration


class VoiceEditorPage(BasePage):
    title = "Voice Editor"
    subtitle = "Edit how a voice speaks. Generate and scripts use this model and delivery."

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self._voice: dict | None = None
        self._loading = False

        header = QHBoxLayout()
        self.voice = VoiceSelector(none_label="Select a voice")
        self.voice.currentIndexChanged.connect(lambda _i: self._voice_changed())
        save = QPushButton("Save voice")
        save.setObjectName("Primary")
        save.clicked.connect(self.save)
        preview = QPushButton("Preview")
        preview.clicked.connect(self.preview)
        use = QPushButton("Use in Generate")
        use.clicked.connect(self.use_in_generate)
        header.addWidget(QLabel("Voice"))
        header.addWidget(self.voice, 1)
        header.addWidget(preview)
        header.addWidget(use)
        header.addWidget(save)
        self.root.addLayout(header)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.root.addWidget(splitter, 1)

        samples_box = QGroupBox("Reference samples")
        samples_layout = QVBoxLayout(samples_box)
        self.sample_hint = QLabel("Cloned voices speak from these recordings. Preset voices use the engine voice.")
        self.sample_hint.setObjectName("Hint")
        self.sample_hint.setWordWrap(True)
        self.samples = QListWidget()
        self.samples.itemActivated.connect(self._play_sample)
        play_sample = QPushButton("Play sample")
        play_sample.clicked.connect(lambda: self._play_sample(self.samples.currentItem()))
        samples_layout.addWidget(self.sample_hint)
        samples_layout.addWidget(self.samples, 1)
        samples_layout.addWidget(play_sample)
        splitter.addWidget(samples_box)

        form_host = QWidget()
        form_layout = QVBoxLayout(form_host)
        form_layout.setContentsMargins(0, 0, 0, 0)

        identity = QGroupBox("Voice and model")
        identity_form = QFormLayout(identity)
        self.name = QLineEdit()
        self.description = QLineEdit()
        self.language = QLineEdit()
        self.model = ModelSelector(default_label="No speaking model")
        self.model.setEnabled(False)
        self.model.setToolTip("A voice stays on the model it was created with.")
        self.engine_voice = QLineEdit()
        self.engine_voice.setPlaceholderText("Kokoro af_heart, Edge en-US-AriaNeural, …")
        identity_form.addRow("Name", self.name)
        identity_form.addRow("Description", self.description)
        identity_form.addRow("Language", self.language)
        identity_form.addRow("Model", self.model)
        identity_form.addRow("Engine voice", self.engine_voice)
        form_layout.addWidget(identity)

        delivery = QGroupBox("Delivery used when this voice generates audio")
        delivery_form = QFormLayout(delivery)
        self.speed = self._spin(0.5, 2.0, 1.0)
        self.pitch = self._spin(0.5, 2.0, 1.0)
        self.energy = self._spin(0.1, 2.0, 1.0)
        self.emotion = QComboBox()
        self.emotion.addItems(list(EMOTIONS))
        self.style = QComboBox()
        self.style.addItems(list(STYLES))
        delivery_form.addRow("Speed", self.speed)
        delivery_form.addRow("Pitch", self.pitch)
        delivery_form.addRow("Energy", self.energy)
        delivery_form.addRow("Emotion", self.emotion)
        delivery_form.addRow("Style", self.style)
        form_layout.addWidget(delivery)

        self.preview_text = QLineEdit("This is how the edited voice sounds with the selected model.")
        form_layout.addWidget(QLabel("Preview line"))
        form_layout.addWidget(self.preview_text)
        form_layout.addStretch(1)
        splitter.addWidget(form_host)
        splitter.setSizes([420, 560])

        self.player = AudioPlayer()
        self.root.addWidget(self.player)
        state.data_changed.connect(
            lambda what: self.voice.refresh() if what in ("voices", "settings") and self.isVisible() else None)

    def refresh(self):
        self.voice.refresh()
        self.model.refresh()
        if self.voice.voices_id() is not None:
            self._load(self.voice.voices_id())

    def open_voice(self, voices_id: int):
        self.voice.set_voices_id(voices_id)
        self._load(voices_id)

    def _voice_changed(self):
        if self._loading:
            return
        voices_id = self.voice.voices_id()
        if voices_id is None:
            self._voice = None
            self.samples.clear()
            return
        self._load(voices_id)

    def _load(self, voices_id: int):
        self.run(lambda: voice_service.get(voices_id), self._show, busy=False)

    def _show(self, voice: dict):
        self._loading = True
        self._voice = voice
        self.voice.set_voices_id(voice["voices_id"])
        self.name.setText(voice.get("name") or "")
        self.description.setText(voice.get("description") or "")
        self.language.setText(voice.get("language") or "en")
        self.model.set_model_key(voice.get("model_key"), force=True)
        self.engine_voice.setText(voice.get("engine_voice") or "")
        delivery = voice.get("delivery") or DELIVERY_DEFAULTS
        self.speed.setValue(float(delivery.get("speed", 1.0)))
        self.pitch.setValue(float(delivery.get("pitch", 1.0)))
        self.energy.setValue(float(delivery.get("energy", 1.0)))
        emotion = delivery.get("emotion") or "neutral"
        if emotion in EMOTIONS:
            self.emotion.setCurrentText(emotion)
        style = delivery.get("style") or "default"
        if style in STYLES:
            self.style.setCurrentText(style)
        self.samples.clear()
        for sample in voice.get("samples") or []:
            item = QListWidgetItem(f"{format_duration(sample.get('duration') or 0)}  ·  sample {sample['voice_samples_id']}")
            item.setData(Qt.ItemDataRole.UserRole, sample.get("path"))
            self.samples.addItem(item)
        if voice.get("source") != "clone":
            self.sample_hint.setText("This is a preset voice. The engine voice and model speak it; there are no samples to edit.")
        else:
            self.sample_hint.setText("These recordings are the cloned voice. Delivery and the model below are used when it generates audio.")
        self._loading = False

    def _values(self) -> dict:
        return {
            "name": self.name.text().strip(),
            "description": self.description.text(),
            "language": self.language.text().strip() or "en",
            "engine_voice": self.engine_voice.text().strip() or None,
            "delivery": {
                "speed": self.speed.value(),
                "pitch": self.pitch.value(),
                "energy": self.energy.value(),
                "emotion": self.emotion.currentText(),
                "style": self.style.currentText(),
            },
        }

    def save(self, afterwards=None):
        voice = self._voice
        if not voice:
            self.error("Select a voice first")
            return
        values = self._values()
        if not values["name"]:
            self.error("The voice needs a name")
            return

        def done(saved):
            self._show(saved)
            self.state.notify("voices")
            if afterwards:
                afterwards(saved)

        self.run(lambda: voice_service.update(voice["voices_id"], **values), done)

    def preview(self):
        voice = self._voice
        if not voice:
            self.error("Select a voice first")
            return
        values = self._values()
        text = self.preview_text.text().strip() or "This is how the edited voice sounds."
        request = TTSRequest(
            text=text,
            voices_id=voice["voices_id"],
            model_key=voice.get("model_key"),
            engine_voice=values["engine_voice"],
            **values["delivery"],
        )
        self.follow(tts_service.generate_async(request), lambda result: (
            self.player.load(result["audio"]["path"], f"Preview · {voice['name']}"), self.player.play()))

    def use_in_generate(self):
        self.save(afterwards=lambda saved: self.state.use_voice.emit(saved["voices_id"]))

    def _play_sample(self, item):
        if item is None:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        if path:
            self.player.load(path, item.text())
            self.player.play()

    @staticmethod
    def _spin(low, high, value):
        spin = QDoubleSpinBox()
        spin.setRange(low, high)
        spin.setSingleStep(0.05)
        spin.setDecimals(2)
        spin.setValue(value)
        return spin
