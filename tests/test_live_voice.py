"""Tests for the Live Voice Changer service and UI page."""

import numpy as np
import pytest

from app.constants.live_voice import LIVE_VOICE_PRESETS
from app.services.live_voice_service import GrainPitchShifter, live_voice_service


def test_grain_pitch_shifter_preserves_length_and_shifts():
    shifter = GrainPitchShifter(sample_rate=16000, grain_ms=35.0)
    # 440 Hz test sine
    t = np.arange(1024) / 16000.0
    chunk = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

    # Shift up +6 semitones
    out_high = shifter.process(chunk, 6.0)
    assert len(out_high) == len(chunk)
    assert np.max(np.abs(out_high)) > 0.05

    # Shift down -5 semitones
    out_low = shifter.process(chunk, -5.0)
    assert len(out_low) == len(chunk)
    assert np.max(np.abs(out_low)) > 0.05

    # Bypass (0 semitones)
    out_bypass = shifter.process(chunk, 0.0)
    assert np.allclose(out_bypass, chunk)


def test_live_voice_service_presets_and_parameters():
    presets = live_voice_service.get_presets()
    assert len(presets) >= 8
    keys = [p["key"] for p in presets]
    assert "bypass" in keys
    assert "deep_narrator" in keys
    assert "robot" in keys
    assert "radio" in keys

    # Apply deep narrator preset
    live_voice_service.set_preset("deep_narrator")
    assert live_voice_service.preset_key == "deep_narrator"
    assert live_voice_service.pitch_semitones == pytest.approx(-4.5, abs=0.1)

    # Apply parameters
    live_voice_service.set_parameters(
        pitch_semitones=3.5,
        robot_mod=True,
        filter_mode="radio",
        noise_gate_db=-40.0,
        output_gain=1.2,
    )
    assert live_voice_service.pitch_semitones == pytest.approx(3.5, abs=0.1)
    assert live_voice_service.robot_mod is True
    assert live_voice_service.filter_mode == "radio"
    assert live_voice_service.noise_gate_db == -40.0
    assert live_voice_service.output_gain == pytest.approx(1.2, abs=0.1)


def test_dsp_pipeline_filters_and_effects():
    # Reset to known parameters
    live_voice_service.set_parameters(
        pitch_semitones=0.0,
        robot_mod=False,
        filter_mode="radio",
        noise_gate_db=-55.0,
        output_gain=1.0,
    )
    t = np.arange(1024) / 16000.0
    chunk = (0.4 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)

    # Process audio chunk
    out, in_rms, out_rms, in_peak, out_peak, waveform = live_voice_service.process_audio_chunk(chunk)
    assert len(out) == len(chunk)
    assert in_rms > 0.1
    assert out_rms > 0.1
    assert len(waveform) == 32

    # Test noise gate
    live_voice_service.set_parameters(noise_gate_db=-30.0)
    quiet_chunk = (0.001 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32)
    out_quiet, in_r, out_r, _, _, _ = live_voice_service.process_audio_chunk(quiet_chunk)
    assert out_r < 0.0001  # gated to near zero

    # Test robot modulation
    live_voice_service.set_parameters(noise_gate_db=-60.0, robot_mod=True, filter_mode=None)
    out_robot, _, _, _, _, _ = live_voice_service.process_audio_chunk(chunk)
    assert len(out_robot) == len(chunk)

    # Test raw PCM bytes conversion
    raw_pcm = (chunk * 32767.0).astype(np.int16).tobytes()
    out_bytes, b_in_rms, b_out_rms, _, _, _ = live_voice_service.process_pcm_bytes(raw_pcm)
    assert len(out_bytes) == len(raw_pcm)
    assert b_in_rms > 0.1


def test_live_voice_simulated_stream():
    # Start stream in test_tone mode (headless / CI safe)
    started = live_voice_service.start_stream(test_tone=True)
    assert started is True
    assert live_voice_service.is_streaming() is True

    # Toggle stream
    live_voice_service.toggle_stream()
    assert live_voice_service.is_streaming() is False


def test_live_voice_page_ui(qtbot):
    from app.ui.main_window import AppState
    from app.ui.pages.live_voice_page import LiveVoicePage

    state = AppState()
    page = LiveVoicePage(state)
    qtbot.addWidget(page)

    # Page initialized with Select widgets
    assert page.input_select is not None
    assert page.output_select is not None
    assert page.filter_select is not None

    # Presets
    assert "deep_narrator" in page.preset_buttons
    page.apply_preset_by_key("deep_narrator")
    assert page.pitch_slider.value() == -45

    page.apply_preset_by_key("high_voice")
    assert page.pitch_slider.value() == 60

    # Sliders
    page.pitch_slider.setValue(20)
    assert live_voice_service.pitch_semitones == pytest.approx(2.0, abs=0.1)

    page.gate_slider.setValue(-45)
    assert live_voice_service.noise_gate_db == pytest.approx(-45.0, abs=0.1)

    page.gain_slider.setValue(150)
    assert live_voice_service.output_gain == pytest.approx(1.5, abs=0.1)

    # Level meter update simulation
    page._on_levels_updated(0.3, 0.4, 0.5, 0.6, [0.1] * 32)
    assert page.in_meter._peak == pytest.approx(0.5, abs=0.01)
    assert page.out_meter._peak == pytest.approx(0.6, abs=0.01)

    # Test streaming button toggle in test_tone mode
    page.test_tone_check.setChecked(True)
    page.toggle_streaming()
    assert live_voice_service.is_streaming() is True
    assert "Stop" in page.stream_button.text()

    page.toggle_streaming()
    assert live_voice_service.is_streaming() is False
    assert "Start" in page.stream_button.text()
