"""Piper must remain usable as the low-resource CPU TTS baseline."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

from app.utils.model import PiperBackend, SynthesisRequest


def test_piper_loads_and_synthesizes_without_cuda(tmp_path, monkeypatch):
    model_path = tmp_path / "model.onnx"
    model_path.write_bytes(b"fake model")
    loaded = {}

    class FakeVoice:
        def synthesize_wav(self, text, wav_file, syn_config):
            loaded["text"] = text
            loaded["length_scale"] = syn_config.length_scale
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(22050)
            wav_file.writeframes(b"\\x00\\x00" * 2205)

    class FakePiperVoice:
        @staticmethod
        def load(path, config_path, use_cuda):
            loaded.update(path=path, config_path=config_path, use_cuda=use_cuda)
            return FakeVoice()

    class FakeSynthesisConfig:
        def __init__(self, length_scale):
            self.length_scale = length_scale

    monkeypatch.setitem(
        sys.modules,
        "piper",
        SimpleNamespace(PiperVoice=FakePiperVoice, SynthesisConfig=FakeSynthesisConfig),
    )

    backend = PiperBackend(Path(tmp_path), device="cpu")
    backend.load()
    audio, sample_rate = backend.synthesize(
        SynthesisRequest(text="CPU baseline", speed=1.25),
        None,
    )

    assert loaded["use_cuda"] is False
    assert loaded["path"] == str(model_path)
    assert loaded["config_path"] == f"{model_path}.json"
    assert loaded["text"] == "CPU baseline"
    assert loaded["length_scale"] == 0.8
    assert sample_rate == 22050
    assert audio.dtype == np.float32
    assert audio.shape == (2205,)
