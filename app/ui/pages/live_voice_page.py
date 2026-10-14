"""Live Voice Changer Studio page.

Provides real-time voice pitch-shifting, voice effect presets (Deep Narrator, Chipmunk,
Robot, Walkie-Talkie, Monster, Telephone), microphone and virtual audio cable routing,
noise gating, output gain, and real-time streaming VU meters and oscilloscope visualizers.
"""

from typing import Any

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.constants.live_voice import LIVE_VOICE_PRESETS
from app.services.live_voice_service import live_voice_service
from app.ui import icons, theme
from app.ui.pages import BasePage
from app.ui.widgets.select import Select


class StreamWaveformWidget(QWidget):
    """Real-time live waveform oscilloscope visualizer."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(54)
        self.setMinimumWidth(200)
        self._samples: list[float] = [0.0] * 32

    def set_samples(self, samples: list[float]) -> None:
        self._samples = samples[:32] if samples else [0.0] * 32
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w = rect.width()
        h = rect.height()
        mid_y = h / 2.0

        # Background
        bg = QColor(theme.current().surface)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(rect, 6, 6)

        # Center reference line
        guide_color = QColor(theme.current().border)
        guide_color.setAlpha(60)
        painter.setPen(QPen(guide_color, 1, Qt.PenStyle.DashLine))
        painter.drawLine(0, int(mid_y), w, int(mid_y))

        # Waveform line / bars
        n = len(self._samples)
        if n < 2:
            return

        accent = QColor(theme.current().accent)
        pen = QPen(accent, 2.0, Qt.PenStyle.SolidLine)
        painter.setPen(pen)

        path = QPainterPath()
        dx = w / float(n - 1)
        start_y = mid_y - (self._samples[0] * (h * 0.42))
        path.moveTo(0, max(2.0, min(h - 2.0, start_y)))

        for i in range(1, n):
            x = i * dx
            val = self._samples[i]
            y = mid_y - (val * (h * 0.42))
            path.lineTo(x, max(2.0, min(h - 2.0, y)))

        painter.drawPath(path)


class LevelMeterWidget(QWidget):
    """Real-time stereo/mono VU level meter with green/yellow/red gradient."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        self.label_text = label
        self._level = 0.0
        self._peak = 0.0
        self.setFixedHeight(24)
        self.setMinimumWidth(160)

    def set_level(self, level: float, peak: float) -> None:
        self._level = max(0.0, min(1.0, level * 2.5))  # normalize for visual display
        self._peak = max(0.0, min(1.0, peak))
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        w = rect.width()
        h = rect.height()

        # Background trough
        bg = QColor(theme.current().surface)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(bg))
        painter.drawRoundedRect(rect, 4, 4)

        # Active level fill
        bar_w = int(w * self._level)
        if bar_w > 0:
            grad = QLinearGradient(0, 0, w, 0)
            grad.setColorAt(0.0, QColor("#10b981"))  # green
            grad.setColorAt(0.70, QColor("#10b981"))
            grad.setColorAt(0.85, QColor("#f59e0b"))  # amber
            grad.setColorAt(1.0, QColor("#ef4444"))   # red
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(QRectF(0, 0, bar_w, h), 4, 4)

        # Peak indicator line
        if self._peak > 0.02:
            peak_x = int(w * self._peak)
            peak_color = QColor("#ef4444" if self._peak > 0.9 else "#f59e0b")
            painter.setPen(QPen(peak_color, 2))
            painter.drawLine(peak_x, 0, peak_x, h)

        # Label overlay
        painter.setPen(QColor(theme.current().text))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(rect.adjusted(6, 0, -6, 0), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, self.label_text)


class LiveVoicePage(BasePage):
    """Dedicated interactive UI page for real-time live voice changing."""

    title = "Live Voice Changer"
    subtitle = "Real-time microphone transformation with voice effects, pitch shifting, and streaming VU visualizers."

    def __init__(self, state, parent=None):
        super().__init__(state, parent)
        self.service = live_voice_service

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(16)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        self.root.addWidget(scroll, 1)

        # Top Master Control Header
        master_box = QFrame()
        master_box.setObjectName("Tile")
        mb_layout = QHBoxLayout(master_box)

        status_col = QVBoxLayout()
        self.status_badge = QLabel("OFFLINE")
        self.status_badge.setObjectName("Hint")
        self.status_badge.setStyleSheet("font-weight: bold; font-size: 13px; color: #888;")
        self.stats_label = QLabel("Stream inactive  ·  Latency: ~35 ms  ·  16 kHz mono")
        self.stats_label.setObjectName("Hint")
        status_col.addWidget(self.status_badge)
        status_col.addWidget(self.stats_label)
        mb_layout.addLayout(status_col, 1)

        self.stream_button = QPushButton("Start Live Voice")
        self.stream_button.setObjectName("Primary")
        self.stream_button.setMinimumHeight(44)
        self.stream_button.setMinimumWidth(180)
        self.stream_button.clicked.connect(self.toggle_streaming)
        mb_layout.addWidget(self.stream_button)

        layout.addWidget(master_box)

        # Real-time Visualizers Box
        vis_group = QGroupBox("Live Stream Monitor")
        vg_layout = QVBoxLayout(vis_group)
        self.waveform_widget = StreamWaveformWidget()
        vg_layout.addWidget(self.waveform_widget)

        meters_row = QHBoxLayout()
        self.in_meter = LevelMeterWidget("Input Mic")
        self.out_meter = LevelMeterWidget("Output Stream")
        meters_row.addWidget(self.in_meter, 1)
        meters_row.addWidget(self.out_meter, 1)
        vg_layout.addLayout(meters_row)
        layout.addWidget(vis_group)

        # Device Routing Section
        routing_group = QGroupBox("Audio Input & Output Device Routing")
        rg_layout = QVBoxLayout(routing_group)

        dev_grid = QGridLayout()
        dev_grid.addWidget(QLabel("Input Microphone:"), 0, 0)
        self.input_select = Select()
        self.input_select.currentIndexChanged.connect(self._on_device_changed)
        dev_grid.addWidget(self.input_select, 0, 1)

        dev_grid.addWidget(QLabel("Output Audio Device:"), 1, 0)
        self.output_select = Select()
        self.output_select.currentIndexChanged.connect(self._on_device_changed)
        dev_grid.addWidget(self.output_select, 1, 1)

        refresh_devs = QPushButton("Refresh Devices")
        refresh_devs.clicked.connect(self._populate_devices)
        dev_grid.addWidget(refresh_devs, 0, 2, 2, 1)
        rg_layout.addLayout(dev_grid)

        # Quick actions row for Vox MIC
        mic_actions_row = QHBoxLayout()
        self.vox_mic_btn = QPushButton("Auto-Route to Vox MIC")
        self.vox_mic_btn.setObjectName("Primary")
        self.vox_mic_btn.setToolTip("Route audio directly to a Virtual Microphone for Discord, OBS, or Zoom")
        self.vox_mic_btn.clicked.connect(self.auto_route_to_vox_mic)
        mic_actions_row.addWidget(self.vox_mic_btn)

        self.setup_mic_btn = QPushButton("Vox MIC Driver Setup…")
        self.setup_mic_btn.setToolTip("Install or configure the Virtual Audio Cable driver")
        self.setup_mic_btn.clicked.connect(self.setup_virtual_mic_dialog)
        mic_actions_row.addWidget(self.setup_mic_btn)

        mic_actions_row.addStretch()
        rg_layout.addLayout(mic_actions_row)

        # Virtual Cable / Streaming Hint Banner
        hint_box = QFrame()
        hint_box.setObjectName("Tile")
        hb_layout = QHBoxLayout(hint_box)
        hint_icon = QLabel()
        hint_icon.setPixmap(icons.icon("speaker", theme.current().accent, size=24).pixmap(24, 24))
        hint_text = QLabel(
            "<b>Route to Discord, OBS, Games or Zoom:</b> Select a <i>Virtual Audio Cable</i> "
            "(e.g. VB-CABLE Input or VoiceMeeter) as Output Device above. In Discord or OBS settings, "
            "choose that same Virtual Cable as your microphone input to speak with your transformed voice live!"
        )
        hint_text.setWordWrap(True)
        hb_layout.addWidget(hint_icon)
        hb_layout.addWidget(hint_text, 1)
        rg_layout.addWidget(hint_box)

        layout.addWidget(routing_group)

        # Voice Presets Grid
        preset_group = QGroupBox("Voice Presets")
        pg_layout = QGridLayout(preset_group)
        self.preset_buttons: dict[str, QPushButton] = {}
        presets = self.service.get_presets()
        for idx, preset in enumerate(presets):
            btn = QPushButton(preset["name"])
            btn.setToolTip(preset["description"])
            btn.setCheckable(True)
            k = preset["key"]
            btn.clicked.connect(lambda checked=False, key=k: self.apply_preset_by_key(key))
            self.preset_buttons[k] = btn
            row, col = divmod(idx, 3)
            pg_layout.addWidget(btn, row, col)

        layout.addWidget(preset_group)

        # DSP Fine-Tuning Controls
        controls_group = QGroupBox("Voice Fine-Tuning")
        cg_layout = QFormLayout(controls_group)

        # Pitch shift slider
        pitch_box = QHBoxLayout()
        self.pitch_slider = QSlider(Qt.Orientation.Horizontal)
        self.pitch_slider.setRange(-120, 120)  # -12.0 to +12.0 semitones
        self.pitch_slider.setValue(int(self.service.pitch_semitones * 10))
        self.pitch_slider.valueChanged.connect(self._on_pitch_changed)
        self.pitch_label = QLabel(f"{self.service.pitch_semitones:+.1f} semitones")
        self.pitch_label.setFixedWidth(100)
        pitch_box.addWidget(self.pitch_slider, 1)
        pitch_box.addWidget(self.pitch_label)
        cg_layout.addRow("Pitch Shift:", pitch_box)

        # Robot mode checkbox
        self.robot_check = QCheckBox("Robot Ring Modulation (60 Hz Carrier)")
        self.robot_check.setChecked(self.service.robot_mod)
        self.robot_check.toggled.connect(self._on_robot_toggled)
        cg_layout.addRow("Robotic Timbre:", self.robot_check)

        # Filter mode selector
        self.filter_select = Select()
        self.filter_select.addItem("Full Frequency (Clean)", "")
        self.filter_select.addItem("Deep Bass Boost", "bass_boost")
        self.filter_select.addItem("Treble / Squeak Boost", "treble_boost")
        self.filter_select.addItem("Walkie-Talkie Radio (350Hz–3.2kHz)", "radio")
        self.filter_select.addItem("Vintage Telephone (300Hz–3.4kHz)", "telephone")
        self.filter_select.addItem("Cosmic Alien Modulator", "alien")
        self.filter_select.currentIndexChanged.connect(self._on_filter_changed)
        cg_layout.addRow("Audio Filter Mode:", self.filter_select)

        # Noise gate slider
        gate_box = QHBoxLayout()
        self.gate_slider = QSlider(Qt.Orientation.Horizontal)
        self.gate_slider.setRange(-60, -20)
        self.gate_slider.setValue(int(self.service.noise_gate_db))
        self.gate_slider.valueChanged.connect(self._on_gate_changed)
        self.gate_label = QLabel(f"{self.service.noise_gate_db:.0f} dB")
        self.gate_label.setFixedWidth(100)
        gate_box.addWidget(self.gate_slider, 1)
        gate_box.addWidget(self.gate_label)
        cg_layout.addRow("Noise Gate Threshold:", gate_box)

        # Output gain slider
        gain_box = QHBoxLayout()
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(0, 200)
        self.gain_slider.setValue(int(self.service.output_gain * 100))
        self.gain_slider.valueChanged.connect(self._on_gain_changed)
        self.gain_label = QLabel(f"{int(self.service.output_gain * 100)}%")
        self.gain_label.setFixedWidth(100)
        gain_box.addWidget(self.gain_slider, 1)
        gain_box.addWidget(self.gain_label)
        cg_layout.addRow("Output Gain / Limiter:", gain_box)

        # Test Tone Preview
        self.test_tone_check = QCheckBox("Test Tone Simulation (Preview without speaking)")
        self.test_tone_check.toggled.connect(self._on_test_tone_toggled)
        cg_layout.addRow("Offline Preview:", self.test_tone_check)

        layout.addWidget(controls_group)
        layout.addStretch()

        # Wire live signals
        self.service.levels_updated.connect(self._on_levels_updated)
        self.service.state_changed.connect(self._on_state_changed)

        self._populate_devices()
        self._highlight_active_preset()

    # ------------------------------------------------------------ Device population

    def _populate_devices(self) -> None:
        self.input_select.blockSignals(True)
        self.output_select.blockSignals(True)

        self.input_select.clear()
        for dev in self.service.get_input_devices():
            prefix = "🎙️ [Default] " if dev["is_default"] else ("📻 [Virtual] " if dev["is_virtual"] else "🎤 ")
            self.input_select.addItem(f"{prefix}{dev['description']}", dev["device"])
            if dev["is_default"]:
                self.input_select.setCurrentIndex(self.input_select.count() - 1)

        self.output_select.clear()
        for dev in self.service.get_output_devices():
            if dev["is_virtual"]:
                prefix = "🎙️ [Vox MIC] "
            elif dev["is_default"]:
                prefix = "🔊 [Default] "
            else:
                prefix = "🎧 "
            self.output_select.addItem(f"{prefix}{dev['description']}", dev["device"])
            if dev["is_default"]:
                self.output_select.setCurrentIndex(self.output_select.count() - 1)

        self.input_select.blockSignals(False)
        self.output_select.blockSignals(False)

    def auto_route_to_vox_mic(self) -> None:
        """Automatically find and select the Vox MIC / Virtual Cable output device."""
        virt_dev = self.service.get_virtual_output_device()
        if virt_dev is not None:
            for idx in range(self.output_select.count()):
                dev = self.output_select.itemData(idx)
                if dev and hasattr(dev, "description") and any(
                    k in dev.description().lower() for k in ("cable", "virtual", "voicemeeter", "voxlabs", "vox mic")
                ):
                    self.output_select.setCurrentIndex(idx)
                    break
        else:
            self.setup_virtual_mic_dialog()

    def setup_virtual_mic_dialog(self) -> None:
        """Guide the user through setting up a Virtual Microphone (Vox MIC) endpoint in Windows."""
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtWidgets import QMessageBox

        msg = QMessageBox(self)
        msg.setWindowTitle("Vox MIC — Virtual Microphone Setup")
        msg.setText("<h3>Use VoxLabs as 'Vox MIC' in other applications</h3>")
        has_virt = self.service.has_virtual_mic()
        status_text = (
            "<p style='color: #10b981; font-weight: bold;'>✔ Virtual Audio Cable detected on this computer!</p>"
            if has_virt
            else "<p style='color: #f59e0b; font-weight: bold;'>⚠ Virtual Audio Cable driver not detected yet.</p>"
        )
        msg.setInformativeText(
            f"{status_text}"
            "<p>To let Discord, Zoom, OBS, CS:GO, or browsers hear your transformed voice in real time, "
            "Windows needs a <b>Virtual Audio Device</b> to route audio from VoxLabs into other apps:</p>"
            "<ol>"
            "<li><b>Install the free VB-CABLE driver</b> (standard virtual audio device for Windows).</li>"
            "<li>In VoxLabs: Click <b>'Auto-Route to Vox MIC'</b> (or select 'CABLE Input' as Output Device).</li>"
            "<li>In Discord / Zoom / Games: In Voice Settings, select <b>'CABLE Output'</b> as your Microphone!</li>"
            "</ol>"
            "<p>Everything you say will then be transformed live by VoxLabs and delivered into your game or call!</p>"
        )
        download_btn = msg.addButton("Download Free VB-CABLE Driver…", QMessageBox.ButtonRole.ActionRole)
        msg.addButton(QMessageBox.StandardButton.Close)
        msg.exec()
        if msg.clickedButton() is download_btn:
            QDesktopServices.openUrl(QUrl("https://vb-audio.com/Cable/"))

    def _on_device_changed(self) -> None:
        if self.service.is_streaming():
            # Restart with newly chosen device
            self.service.stop_stream()
            self.start_streaming()

    # ------------------------------------------------------------ Streaming controls

    def toggle_streaming(self) -> None:
        if self.service.is_streaming():
            self.service.stop_stream()
        else:
            self.start_streaming()

    def start_streaming(self) -> None:
        in_dev = self.input_select.currentData()
        out_dev = self.output_select.currentData()
        test_tone = self.test_tone_check.isChecked()
        self.service.start_stream(in_dev, out_dev, test_tone=test_tone)

    def _on_state_changed(self, streaming: bool) -> None:
        if streaming:
            self.stream_button.setText("Stop Live Voice")
            self.stream_button.setObjectName("Danger")
            self.status_badge.setText("● STREAMING LIVE")
            self.status_badge.setStyleSheet("font-weight: bold; font-size: 13px; color: #10b981;")
            preset_name = self.service.preset_key.replace("_", " ").title()
            self.stats_label.setText(f"Active preset: {preset_name}  ·  Latency: ~35 ms  ·  16 kHz mono")
        else:
            self.stream_button.setText("Start Live Voice")
            self.stream_button.setObjectName("Primary")
            self.status_badge.setText("OFFLINE")
            self.status_badge.setStyleSheet("font-weight: bold; font-size: 13px; color: #888;")
            self.stats_label.setText("Stream inactive  ·  Latency: ~35 ms  ·  16 kHz mono")
            self.in_meter.set_level(0.0, 0.0)
            self.out_meter.set_level(0.0, 0.0)
            self.waveform_widget.set_samples([0.0] * 32)
        style = self.stream_button.style()
        if style is not None:
            style.unpolish(self.stream_button)
            style.polish(self.stream_button)

    def _on_levels_updated(
        self, in_rms: float, out_rms: float, in_peak: float, out_peak: float, waveform: list[float]
    ) -> None:
        self.in_meter.set_level(in_rms, in_peak)
        self.out_meter.set_level(out_rms, out_peak)
        self.waveform_widget.set_samples(waveform)

    # ------------------------------------------------------------ Preset handling

    def apply_preset_by_key(self, key: str) -> None:
        self.service.set_preset(key)
        self.pitch_slider.blockSignals(True)
        self.pitch_slider.setValue(int(self.service.pitch_semitones * 10))
        self.pitch_label.setText(f"{self.service.pitch_semitones:+.1f} semitones")
        self.pitch_slider.blockSignals(False)

        self.robot_check.blockSignals(True)
        self.robot_check.setChecked(self.service.robot_mod)
        self.robot_check.blockSignals(False)

        idx = self.filter_select.findData(self.service.filter_mode or "")
        if idx >= 0:
            self.filter_select.blockSignals(True)
            self.filter_select.setCurrentIndex(idx)
            self.filter_select.blockSignals(False)

        self._highlight_active_preset()
        if self.service.is_streaming():
            self._on_state_changed(True)

    def _highlight_active_preset(self) -> None:
        active_key = self.service.preset_key
        for key, btn in self.preset_buttons.items():
            btn.setChecked(key == active_key)

    # ------------------------------------------------------------ Parameter handlers

    def _on_pitch_changed(self, value: int) -> None:
        semitones = value / 10.0
        self.pitch_label.setText(f"{semitones:+.1f} semitones")
        self.service.set_parameters(pitch_semitones=semitones)

    def _on_robot_toggled(self, checked: bool) -> None:
        self.service.set_parameters(robot_mod=checked)

    def _on_filter_changed(self) -> None:
        mode = self.filter_select.currentData() or None
        self.service.set_parameters(filter_mode=mode)

    def _on_gate_changed(self, value: int) -> None:
        self.gate_label.setText(f"{value} dB" if value > -59 else "Off")
        self.service.set_parameters(noise_gate_db=float(value))

    def _on_gain_changed(self, value: int) -> None:
        gain = value / 100.0
        self.gain_label.setText(f"{value}%")
        self.service.set_parameters(output_gain=gain)

    def _on_test_tone_toggled(self, checked: bool) -> None:
        if self.service.is_streaming():
            self.service.stop_stream()
            self.start_streaming()

    # ------------------------------------------------------------ Refresh and lifecycle

    def refresh(self) -> None:
        self._populate_devices()
        self._highlight_active_preset()
        self._on_state_changed(self.service.is_streaming())

    def refresh_icons(self) -> None:
        self.stream_button.setIcon(icons.icon("live_voice", theme.current().accent_text, size=16))
