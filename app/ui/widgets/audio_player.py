"""Transport + playback for a single audio file (QtMultimedia)."""

from pathlib import Path

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSlider, QWidget

from app.services.system_service import system_service
from app.ui import icons, theme
from app.utils.time import format_duration


def output_device():
    wanted = system_service.get_setting("output_device")
    for device in QMediaDevices.audioOutputs():
        if device.description() == wanted:
            return device
    return QMediaDevices.defaultAudioOutput()


class AudioPlayer(QWidget):
    """Play / pause / stop / seek, with optional looping of a [start, end] range."""

    position_changed = Signal(float)  # seconds

    def __init__(self, parent=None, compact: bool = False):
        super().__init__(parent)
        self.output = QAudioOutput(output_device(), self)
        self.player = QMediaPlayer(self)
        self.player.setAudioOutput(self.output)
        self._range: tuple[float, float] | None = None
        self._loop = False

        self.play_button = QPushButton()
        self.play_button.setObjectName("Primary")
        self.play_button.setToolTip("Play / pause (Space)")
        self.play_button.clicked.connect(self.toggle)
        self.stop_button = QPushButton()
        self.stop_button.setToolTip("Stop")
        self.stop_button.clicked.connect(self.stop)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(lambda ms: self.player.setPosition(ms))
        self.time_label = QLabel("0:00.0 / 0:00.0")
        self.title = QLabel("")
        self.title.setMinimumWidth(40 if compact else 120)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.play_button)
        layout.addWidget(self.stop_button)
        if not compact:
            layout.addWidget(self.title)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.time_label)

        self.player.positionChanged.connect(self._on_position)
        self.player.durationChanged.connect(lambda ms: self.slider.setRange(0, ms))
        self.player.playbackStateChanged.connect(self._on_state)
        self.refresh_icons()
        self.setEnabled(False)

    def refresh_icons(self) -> None:
        colors = theme.current()
        playing = self.is_playing()
        self.play_button.setIcon(icons.icon("pause" if playing else "play", colors.accent_text))
        self.stop_button.setIcon(icons.icon("stop"))

    # ------------------------------------------------------------ public

    def load(self, path: str | Path | None, title: str = "") -> None:
        self.stop()
        if not path:
            self.player.setSource(QUrl())
            self.setEnabled(False)
            self.title.setText("")
            return
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.title.setText(title or Path(path).stem)
        self.setEnabled(True)

    def play(self, start: float | None = None) -> None:
        if start is not None:
            self.player.setPosition(int(start * 1000))
        self.player.play()

    def play_range(self, start: float, end: float, loop: bool = False) -> None:
        self._range, self._loop = (start, end), loop
        self.play(start)

    def clear_range(self) -> None:
        self._range, self._loop = None, False

    def toggle(self) -> None:
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def stop(self) -> None:
        self.player.stop()
        self.clear_range()

    def seek(self, seconds: float) -> None:
        self.player.setPosition(int(max(0.0, seconds) * 1000))

    def position(self) -> float:
        return self.player.position() / 1000

    def is_playing(self) -> bool:
        return self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    # ------------------------------------------------------------ internals

    def _on_position(self, ms: int) -> None:
        if not self.slider.isSliderDown():
            self.slider.setValue(ms)
        self.time_label.setText(f"{format_duration(ms / 1000)} / {format_duration(self.player.duration() / 1000)}")
        seconds = ms / 1000
        if self._range and seconds >= self._range[1]:
            if self._loop:
                self.player.setPosition(int(self._range[0] * 1000))
            else:
                self.player.pause()
                self.clear_range()
        self.position_changed.emit(seconds)

    def _on_state(self, _state) -> None:
        self.refresh_icons()
