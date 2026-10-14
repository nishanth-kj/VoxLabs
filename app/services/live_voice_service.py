"""Real-time streaming audio / live voice changer service.

Captures microphone audio via QAudioSource, applies low-latency DSP transformations
(granular pitch shifting, ring modulation, filter emulation, noise gating, gain/limiting),
and routes the transformed audio in real time to selected output devices (e.g. speakers,
headphones, or virtual audio cables for Discord, OBS, and games) via QAudioSink.
"""

import math
import sys
import threading
from pathlib import Path
from typing import Any

import numpy as np
from PySide6.QtCore import QByteArray, QIODevice, QObject, QTimer, Signal
from PySide6.QtMultimedia import (
    QAudioDevice,
    QAudioFormat,
    QAudioSink,
    QAudioSource,
    QMediaDevices,
)
from scipy import signal

from app.constants.live_voice import LIVE_VOICE_PRESETS
from app.exceptions import service_error
from app.utils.files import data_dir
from app.utils.logger import logger


class GrainPitchShifter:
    """Low-latency granular overlap-add pitch shifter designed for real-time streaming."""

    def __init__(self, sample_rate: int = 16000, grain_ms: float = 35.0):
        self.sr = sample_rate
        self.grain_size = int(sample_rate * grain_ms / 1000.0)
        if self.grain_size % 2 != 0:
            self.grain_size += 1
        self.window = np.hanning(self.grain_size).astype(np.float32)
        self.history = np.zeros(self.grain_size, dtype=np.float32)

    def reset(self) -> None:
        self.history.fill(0.0)

    def process(self, chunk: np.ndarray, semitones: float) -> np.ndarray:
        if abs(semitones) < 0.08:
            return chunk
        factor = 2.0 ** (semitones / 12.0)
        combined = np.concatenate([self.history, chunk])
        self.history = chunk[-self.grain_size:].copy() if len(chunk) >= self.grain_size else combined[-self.grain_size:].copy()

        hop_out = max(1, self.grain_size // 4)
        hop_in = max(1, int(hop_out * factor))

        out_len = len(chunk)
        output = np.zeros(out_len + self.grain_size, dtype=np.float32)
        norm = np.zeros(out_len + self.grain_size, dtype=np.float32)

        in_pos = 0
        out_pos = 0
        comb_len = len(combined)
        while in_pos + self.grain_size <= comb_len and out_pos < out_len:
            grain = combined[in_pos:in_pos + self.grain_size] * self.window
            output[out_pos:out_pos + self.grain_size] += grain
            norm[out_pos:out_pos + self.grain_size] += self.window
            in_pos += hop_in
            out_pos += hop_out

        mask = norm[:out_len] > 1e-4
        res = np.zeros(out_len, dtype=np.float32)
        res[mask] = output[:out_len][mask] / norm[:out_len][mask]
        res[~mask] = chunk[~mask]
        return res


class LiveVoiceService(QObject):
    """Singleton service providing real-time voice modification and stream routing."""

    # in_rms, out_rms, in_peak, out_peak, waveform_chunk
    levels_updated = Signal(float, float, float, float, list)
    state_changed = Signal(bool)
    error_occurred = Signal(str)

    def __init__(self):
        super().__init__()
        self.sample_rate = 16000
        self.channels = 1
        self.chunk_size = 1024  # ~64ms at 16kHz

        # DSP state
        self._pitch_shifter = GrainPitchShifter(self.sample_rate)
        self._robot_phase = 0.0
        self._radio_zi: np.ndarray | None = None
        self._alien_phase = 0.0

        # Stream parameters
        self.preset_key: str = "deep_narrator"
        self.pitch_semitones: float = -4.5
        self.robot_mod: bool = False
        self.filter_mode: str | None = "bass_boost"
        self.noise_gate_db: float = -48.0
        self.output_gain: float = 1.0
        self.monitor_loopback: bool = False

        # Qt Multimedia objects
        self._source: QAudioSource | None = None
        self._sink: QAudioSink | None = None
        self._input_io: QIODevice | None = None
        self._output_io: QIODevice | None = None
        self._streaming: bool = False
        self._lock = threading.Lock()

        # Simulated test-stream timer for environments without live microphones
        self._test_timer: QTimer | None = None
        self._simulated_phase = 0.0

    @staticmethod
    def _dev_id_to_str(dev: Any, fallback: str) -> str:
        try:
            if hasattr(dev, "id"):
                raw_id = dev.id()
                if hasattr(raw_id, "toStdString"):
                    return str(raw_id.toStdString())
                if hasattr(raw_id, "data"):
                    raw_data: Any = raw_id.data()
                    if isinstance(raw_data, (bytes, bytearray)):
                        return raw_data.decode("utf-8", "ignore")
                    if isinstance(raw_data, memoryview):
                        return raw_data.tobytes().decode("utf-8", "ignore")
            return fallback
        except Exception:
            return fallback

    @staticmethod
    def _butter_ba(order: int, wn: Any, btype: str = "lowpass") -> tuple[np.ndarray, np.ndarray]:
        ba_filt: Any = signal.butter(order, wn, btype=btype, output="ba")
        b = np.asarray(ba_filt[0], dtype=np.float64)
        a = np.asarray(ba_filt[1], dtype=np.float64)
        return b, a

    # ------------------------------------------------------------ Device discovery

    def get_input_devices(self) -> list[dict[str, Any]]:
        """List all available audio input devices (microphones)."""
        try:
            devices = QMediaDevices.audioInputs()
            default = QMediaDevices.defaultAudioInput()
            result = []
            for dev in devices:
                desc = dev.description()
                is_def = dev.id() == default.id() if hasattr(dev, "id") else False
                dev_id_str = self._dev_id_to_str(dev, desc)
                result.append({
                    "id": dev_id_str,
                    "description": desc,
                    "is_default": is_def,
                    "is_virtual": any(k in desc.lower() for k in ("cable", "virtual", "voicemeeter", "voxlabs", "vox mic")),
                    "device": dev,
                })
            return result
        except Exception as exc:
            logger.error("Failed to list audio input devices", exc_info=exc)
            return []

    def get_output_devices(self) -> list[dict[str, Any]]:
        """List all available audio output devices (speakers, virtual cables)."""
        try:
            devices = QMediaDevices.audioOutputs()
            default = QMediaDevices.defaultAudioOutput()
            result = []
            for dev in devices:
                desc = dev.description()
                is_def = dev.id() == default.id() if hasattr(dev, "id") else False
                dev_id_str = self._dev_id_to_str(dev, desc)
                result.append({
                    "id": dev_id_str,
                    "description": desc,
                    "is_default": is_def,
                    "is_virtual": any(k in desc.lower() for k in ("cable", "virtual", "voicemeeter", "voxlabs", "vox mic")),
                    "device": dev,
                })
            return result
        except Exception as exc:
            logger.error("Failed to list audio output devices", exc_info=exc)
            return []

    def has_virtual_mic(self) -> bool:
        """Check whether any Virtual Audio Cable / Vox MIC device is installed and available."""
        return any(dev["is_virtual"] for dev in self.get_output_devices())

    def get_virtual_output_device(self) -> QAudioDevice | None:
        """Return the first detected Virtual Audio Cable device."""
        for dev in self.get_output_devices():
            if dev["is_virtual"]:
                return dev["device"]
        return None

    # ------------------------------------------------------------ Driver installation & uninstallation

    def get_driver_folder(self) -> Path:
        """Directory where the Virtual Audio Cable driver package is stored."""
        folder = data_dir() / "drivers" / "vbcable"
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def get_driver_installer_exe(self) -> Path | None:
        """Find the 64-bit or 32-bit driver installer executable if present."""
        folder = self.get_driver_folder()
        for name in ("VBCABLE_Setup_x64.exe", "VBCABLE_Setup.exe"):
            candidate = folder / name
            if candidate.exists() and candidate.stat().st_size > 10_000:
                return candidate
        return None

    def download_and_extract_driver(self) -> Path:
        """Download and extract the official VB-CABLE driver pack."""
        installer = self.get_driver_installer_exe()
        if installer is not None:
            return installer

        import io
        import ssl
        import urllib.request
        import zipfile

        url = "https://download.vb-audio.com/Download_CABLE/VBCABLE_Driver_Pack45.zip"
        logger.info(f"Downloading Virtual Audio Driver package from {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        ctx = ssl.create_default_context()
        try:
            import certifi
            ctx.load_verify_locations(certifi.where())
        except Exception:
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = resp.read()

        folder = self.get_driver_folder()
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            zf.extractall(folder)

        installer = self.get_driver_installer_exe()
        if installer is None:
            raise RuntimeError("Driver package extracted but VBCABLE_Setup_x64.exe was not found.")
        logger.info(f"Virtual Audio Driver package ready at {installer}")
        return installer

    def install_virtual_driver(self) -> tuple[bool, str]:
        """Launch the Virtual Audio Cable driver installer with Windows administrator privileges."""
        try:
            if sys.platform != "win32":
                return False, "Virtual Audio Cable driver installer is designed for Windows."

            installer = self.download_and_extract_driver()

            import ctypes

            logger.info(f"Launching driver installer with UAC: {installer}")
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", str(installer), "-i", str(installer.parent), 1
            )
            if ret > 32:
                return True, "Driver installer launched. Please approve the Windows Administrator prompt to complete installation."
            elif ret == 1223:
                return False, "Installation was cancelled by the user."
            else:
                return False, f"Windows ShellExecute failed with error code: {ret}"
        except Exception as exc:
            logger.error("Failed to run virtual driver installer", exc_info=exc)
            raise service_error(exc, "live_voice_service.install_virtual_driver")

    def uninstall_virtual_driver(self) -> tuple[bool, str]:
        """Launch the Virtual Audio Cable driver uninstaller with Windows administrator privileges."""
        try:
            if sys.platform != "win32":
                return False, "Virtual Audio Cable driver uninstaller is designed for Windows."

            installer = self.download_and_extract_driver()

            import ctypes

            logger.info(f"Launching driver uninstaller with UAC: {installer}")
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", str(installer), "-u", str(installer.parent), 1
            )
            if ret > 32:
                return True, "Driver uninstaller launched. Please approve the Windows Administrator prompt to remove the driver."
            elif ret == 1223:
                return False, "Uninstallation was cancelled by the user."
            else:
                return False, f"Windows ShellExecute failed with error code: {ret}"
        except Exception as exc:
            logger.error("Failed to run virtual driver uninstaller", exc_info=exc)
            raise service_error(exc, "live_voice_service.uninstall_virtual_driver")

    def get_presets(self) -> list[dict[str, Any]]:
        """Return available live voice presets."""
        return LIVE_VOICE_PRESETS

    # ------------------------------------------------------------ Parameter controls

    def set_preset(self, key: str) -> None:
        """Apply a preset by key."""
        preset = next((p for p in LIVE_VOICE_PRESETS if p["key"] == key), None)
        if preset:
            self.preset_key = key
            self.pitch_semitones = float(preset["pitch_semitones"])
            self.robot_mod = bool(preset["robot_mod"])
            self.filter_mode = preset["filter_mode"]
            logger.debug(f"Live voice preset set to: {preset['name']}")

    def set_parameters(
        self,
        pitch_semitones: float | None = None,
        robot_mod: bool | None = None,
        filter_mode: str | None = None,
        noise_gate_db: float | None = None,
        output_gain: float | None = None,
        monitor_loopback: bool | None = None,
    ) -> None:
        """Dynamically update DSP settings while streaming."""
        if pitch_semitones is not None:
            self.pitch_semitones = float(max(-12.0, min(12.0, pitch_semitones)))
        if robot_mod is not None:
            self.robot_mod = bool(robot_mod)
        if filter_mode is not None:
            self.filter_mode = filter_mode
        if noise_gate_db is not None:
            self.noise_gate_db = float(max(-60.0, min(-20.0, noise_gate_db)))
        if output_gain is not None:
            self.output_gain = float(max(0.0, min(2.5, output_gain)))
        if monitor_loopback is not None:
            self.monitor_loopback = bool(monitor_loopback)

    # ------------------------------------------------------------ Streaming lifecycle

    def is_streaming(self) -> bool:
        return self._streaming

    def start_stream(
        self,
        input_device: QAudioDevice | None = None,
        output_device: QAudioDevice | None = None,
        test_tone: bool = False,
    ) -> bool:
        """Start capturing microphone audio, transforming it, and sending it to output."""
        try:
            with self._lock:
                if self._streaming:
                    return True

                self._pitch_shifter.reset()
                self._robot_phase = 0.0
                self._radio_zi = None
                self._alien_phase = 0.0

                if test_tone or not QMediaDevices.audioInputs():
                    # Simulated stream for tests or test-tone preview
                    self._start_simulated_stream()
                    self._streaming = True
                    self.state_changed.emit(True)
                    logger.info("Live voice test streaming started")
                    return True

                format_ = QAudioFormat()
                format_.setSampleRate(self.sample_rate)
                format_.setChannelCount(self.channels)
                format_.setSampleFormat(QAudioFormat.SampleFormat.Int16)

                in_dev = input_device or QMediaDevices.defaultAudioInput()
                out_dev = output_device or QMediaDevices.defaultAudioOutput()

                if in_dev.isNull():
                    self._start_simulated_stream()
                    self._streaming = True
                    self.state_changed.emit(True)
                    return True

                self._source = QAudioSource(in_dev, format_, self)
                self._source.setBufferSize(self.chunk_size * 4)

                self._sink = QAudioSink(out_dev, format_, self)
                self._sink.setBufferSize(self.chunk_size * 4)

                self._input_io = self._source.start()
                self._output_io = self._sink.start()

                if self._input_io is not None:
                    self._input_io.readyRead.connect(self._on_input_ready)

                self._streaming = True
                self.state_changed.emit(True)
                logger.info(
                    f"Live voice streaming started: '{in_dev.description()}' -> '{out_dev.description()}'"
                )
                return True
        except Exception as exc:
            self.stop_stream()
            logger.error("Failed to start live voice stream", exc_info=exc)
            self.error_occurred.emit(str(exc))
            raise service_error(exc, "live_voice_service.start_stream")

    def stop_stream(self) -> None:
        """Stop capturing and streaming audio."""
        try:
            with self._lock:
                if not self._streaming and self._source is None and self._sink is None:
                    return

                if self._test_timer is not None:
                    self._test_timer.stop()
                    self._test_timer.deleteLater()
                    self._test_timer = None

                if self._source is not None:
                    try:
                        self._source.stop()
                        self._source.deleteLater()
                    except Exception:
                        pass
                    self._source = None
                    self._input_io = None

                if self._sink is not None:
                    try:
                        self._sink.stop()
                        self._sink.deleteLater()
                    except Exception:
                        pass
                    self._sink = None
                    self._output_io = None

                self._streaming = False
                self.state_changed.emit(False)
                # Emit 0 level
                self.levels_updated.emit(0.0, 0.0, 0.0, 0.0, [0.0] * 32)
                logger.info("Live voice streaming stopped")
        except Exception as exc:
            logger.error("Failed to stop live voice stream cleanly", exc_info=exc)

    def toggle_stream(self) -> bool:
        """Toggle live voice streaming on or off."""
        if self.is_streaming():
            self.stop_stream()
            return False
        else:
            return self.start_stream()

    # ------------------------------------------------------------ Audio processing callback

    def _on_input_ready(self) -> None:
        if not self._streaming or self._input_io is None:
            return
        try:
            qba = self._input_io.readAll()
            if qba.isEmpty():
                return
            raw_data: Any = qba.data()
            if isinstance(raw_data, (bytes, bytearray)):
                raw_bytes = bytes(raw_data)
            elif isinstance(raw_data, memoryview):
                raw_bytes = raw_data.tobytes()
            else:
                raw_bytes = b""
            if not raw_bytes:
                return

            transformed_bytes, in_rms, out_rms, in_peak, out_peak, waveform = self.process_pcm_bytes(
                raw_bytes
            )

            if self._output_io is not None and self._sink is not None:
                self._output_io.write(QByteArray(transformed_bytes))

            self.levels_updated.emit(in_rms, out_rms, in_peak, out_peak, waveform)
        except Exception as exc:
            logger.error("Error during real-time chunk DSP processing", exc_info=exc)

    def _start_simulated_stream(self) -> None:
        """Generate test audio chunks when physical mic is not available or in simulation mode."""
        if self._test_timer is not None:
            return
        self._test_timer = QTimer(self)
        self._test_timer.setInterval(50)  # ~20 fps

        def _tick():
            if not self._streaming:
                return
            t = np.arange(self.chunk_size) / self.sample_rate
            carrier = 220.0  # musical A3 tone
            sim_signal = 0.35 * np.sin(2 * np.pi * carrier * t + self._simulated_phase).astype(np.float32)
            self._simulated_phase = (self._simulated_phase + 2 * np.pi * carrier * (self.chunk_size / self.sample_rate)) % (2 * np.pi)

            # Apply DSP
            out_audio, in_rms, out_rms, in_peak, out_peak, waveform = self.process_audio_chunk(sim_signal)
            self.levels_updated.emit(in_rms, out_rms, in_peak, out_peak, waveform)

        self._test_timer.timeout.connect(_tick)
        self._test_timer.start()

    # ------------------------------------------------------------ DSP core pipeline

    def process_pcm_bytes(
        self, raw_bytes: bytes
    ) -> tuple[bytes, float, float, float, float, list[float]]:
        """Process 16-bit signed PCM raw bytes through the DSP pipeline."""
        audio = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        out_audio, in_rms, out_rms, in_peak, out_peak, waveform = self.process_audio_chunk(audio)
        out_int16 = (np.clip(out_audio, -1.0, 1.0) * 32767.0).astype(np.int16)
        return out_int16.tobytes(), in_rms, out_rms, in_peak, out_peak, waveform

    def process_audio_chunk(
        self, chunk: np.ndarray
    ) -> tuple[np.ndarray, float, float, float, float, list[float]]:
        """Process a float32 chunk [-1.0, 1.0] and return (out_chunk, in_rms, out_rms, in_peak, out_peak, waveform)."""
        if len(chunk) == 0:
            return chunk, 0.0, 0.0, 0.0, 0.0, []

        in_peak = float(np.max(np.abs(chunk)))
        in_rms = float(np.sqrt(np.mean(chunk**2)))

        # 1. Noise gate
        gate_db = self.noise_gate_db
        if gate_db > -59.0:
            rms_db = 20.0 * math.log10(in_rms + 1e-6)
            if rms_db < gate_db:
                # Soft knee attenuation
                attenuation = max(0.0, min(1.0, (rms_db - (gate_db - 6.0)) / 6.0))
                chunk = chunk * attenuation
                if attenuation < 0.02:
                    # Mute silent background
                    return np.zeros_like(chunk), in_rms, 0.0, in_peak, 0.0, [0.0] * 32

        # 2. Granular Pitch Shift
        processed = self._pitch_shifter.process(chunk, self.pitch_semitones)

        # 3. Robot ring modulation
        if self.robot_mod:
            n_samples = len(processed)
            carrier_freq = 60.0
            t = np.arange(n_samples) / self.sample_rate
            osc = np.sin(2 * np.pi * carrier_freq * t + self._robot_phase).astype(np.float32)
            self._robot_phase = (self._robot_phase + 2 * np.pi * carrier_freq * (n_samples / self.sample_rate)) % (2 * np.pi)
            processed = processed * osc

        # 4. Filters & Emulations
        if self.filter_mode == "radio":
            nyq = self.sample_rate / 2.0
            low, high = 350.0 / nyq, min(0.95, 3200.0 / nyq)
            b, a = self._butter_ba(2, [low, high], btype="bandpass")
            if self._radio_zi is None or len(self._radio_zi) != max(len(a), len(b)) - 1:
                self._radio_zi = signal.lfilter_zi(b, a)
            filt_out, self._radio_zi = signal.lfilter(b, a, processed, zi=self._radio_zi)
            # Soft saturation
            processed = 1.25 * np.tanh(1.6 * np.asarray(filt_out, dtype=np.float32))
        elif self.filter_mode == "telephone":
            nyq = self.sample_rate / 2.0
            low, high = 300.0 / nyq, min(0.95, 3400.0 / nyq)
            b, a = self._butter_ba(2, [low, high], btype="bandpass")
            if self._radio_zi is None or len(self._radio_zi) != max(len(a), len(b)) - 1:
                self._radio_zi = signal.lfilter_zi(b, a)
            filt_out, self._radio_zi = signal.lfilter(b, a, processed, zi=self._radio_zi)
            processed = np.asarray(filt_out, dtype=np.float32)
        elif self.filter_mode == "bass_boost":
            nyq = self.sample_rate / 2.0
            b, a = self._butter_ba(1, 260.0 / nyq, btype="lowpass")
            lows = np.asarray(signal.lfilter(b, a, processed), dtype=np.float32)
            processed = processed + 0.6 * lows
        elif self.filter_mode == "treble_boost":
            nyq = self.sample_rate / 2.0
            b, a = self._butter_ba(1, min(0.95, 2500.0 / nyq), btype="highpass")
            highs = np.asarray(signal.lfilter(b, a, processed), dtype=np.float32)
            processed = processed + 0.5 * highs
        elif self.filter_mode == "alien":
            n_samples = len(processed)
            mod_freq = 80.0
            t = np.arange(n_samples) / self.sample_rate
            mod = 0.5 * (1.0 + np.sin(2 * np.pi * mod_freq * t + self._alien_phase).astype(np.float32))
            self._alien_phase = (self._alien_phase + 2 * np.pi * mod_freq * (n_samples / self.sample_rate)) % (2 * np.pi)
            processed = processed * (0.5 + mod)

        # 5. Output gain and peak limiter
        processed = processed * self.output_gain
        # Soft-clip limiter to prevent digital distortion
        peaks = np.abs(processed)
        if np.any(peaks > 0.95):
            processed = np.tanh(processed)

        out_peak = float(np.max(np.abs(processed)))
        out_rms = float(np.sqrt(np.mean(processed**2)))

        # Subsample waveform for UI visualization (32 points)
        step = max(1, len(processed) // 32)
        waveform = [float(v) for v in processed[::step][:32]]

        return processed, in_rms, out_rms, in_peak, out_peak, waveform


live_voice_service = LiveVoiceService()
