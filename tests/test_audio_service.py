from pathlib import Path

import numpy as np
import pytest

from app.constants.audio import AI_GENERATED_TAG
from app.exceptions import ValidationError
from app.models.request import AudioExportRequest, AudioProcessRequest
from app.services.audio_service import audio_service
from app.utils import audio as au
from app.utils.hashing import sha256_file


def test_import_keeps_original_and_reads_metadata(voice_wav):
    audio = audio_service.import_file(voice_wav)
    assert audio["source"] == "imported"
    assert audio["duration"] == pytest.approx(4.0, abs=0.01)
    assert audio["sample_rate"] == 24000
    assert audio["channels"] == 1
    assert audio["format"] == "wav"
    assert audio["file_size"] > 0
    assert audio["loudness"] is not None
    assert Path(audio["original_path"]).exists() and Path(audio["path"]).exists()


def test_analyze_reports_quality(voice_wav, tmp_path):
    report = audio_service.analyze(voice_wav)
    assert report["duration"] == pytest.approx(4.0, abs=0.01)
    assert 0 <= report["quality_score"] <= 100
    clipped = tmp_path / "clipped.wav"
    au.save(clipped, np.ones(24000, dtype=np.float32), 24000)
    assert any("Clipping" in issue for issue in audio_service.analyze(clipped)["issues"])


def test_process_is_non_destructive(voice_wav):
    source = audio_service.import_file(voice_wav)
    before = sha256_file(source["path"])
    processed = audio_service.process(AudioProcessRequest(audios_id=source["audios_id"], preset="Podcast"))
    assert processed["audios_id"] != source["audios_id"]
    assert processed["parent_audios_id"] == source["audios_id"]
    assert sha256_file(source["path"]) == before
    assert processed["original_path"] == source["original_path"]
    assert processed["loudness"] == pytest.approx(-16.0, abs=1.5)


def test_steps_can_be_disabled():
    steps = audio_service.resolve_steps({"denoise": None, "limit": {"ceiling_db": -3}}, preset="Podcast")
    assert "denoise" not in steps and steps["limit"] == {"ceiling_db": -3}
    with pytest.raises(ValidationError):
        audio_service.resolve_steps({"reverse": {}})


def test_every_enhancement_step_runs():
    sr = 24000
    y = (0.3 * np.sin(2 * np.pi * 220 * np.arange(sr) / sr)).astype(np.float32)
    steps = {s: {} for s in ("trim_silence", "denoise", "eq", "compress", "deess", "normalize", "limit", "loudness")}
    out = audio_service.process_array(y, sr, steps)
    assert out.dtype == np.float32 and np.abs(out).max() <= 1.0 and out.size > 0


def test_edit_ops():
    sr = 1000
    y = np.arange(3000, dtype=np.float32) / 3000
    clip_path = audio_service.save_clip(y[:500], sr)
    assert audio_service.apply_edit_ops(y, sr, [{"op": "delete", "start": 1, "end": 2}]).size == 2000
    assert audio_service.apply_edit_ops(y, sr, [{"op": "crop", "start": 1, "end": 2}]).size == 1000
    assert audio_service.apply_edit_ops(y, sr, [{"op": "insert", "at": 1, "clip": clip_path}]).size == 3500
    assert audio_service.apply_edit_ops(y, sr, [{"op": "duplicate", "start": 0, "end": 1}]).size == 4000
    moved = audio_service.apply_edit_ops(y, sr, [{"op": "move", "start": 0, "end": 1, "to": 2}])
    assert moved.size == 3000 and moved[0] == pytest.approx(y[1000])
    quiet = audio_service.apply_edit_ops(y, sr, [{"op": "gain", "start": 0, "end": 3, "db": -6}])
    assert quiet[-1] == pytest.approx(y[-1] * 10 ** (-6 / 20), rel=1e-3)
    with pytest.raises(ValidationError):
        audio_service.apply_edit_ops(y, sr, [{"op": "explode"}])


def test_render_edits_split_join_and_export(voice_wav, tmp_path):
    source = audio_service.import_file(voice_wav)
    edited = audio_service.render_edits(source["audios_id"], [{"op": "delete", "start": 0, "end": 1}])
    assert edited["duration"] == pytest.approx(3.0, abs=0.01)
    a, b = audio_service.split(source["audios_id"], 1.5)
    assert a["duration"] + b["duration"] == pytest.approx(4.0, abs=0.01)
    joined = audio_service.join([a["audios_id"], b["audios_id"]], gap_ms=500)
    assert joined["duration"] == pytest.approx(4.5, abs=0.01)
    exported = audio_service.export(AudioExportRequest(audios_id=joined["audios_id"], format="flac"), tmp_path / "out.flac")
    assert Path(exported).exists() and au.info(exported)["format"] == "flac"


def test_ai_generated_export_is_tagged(tmp_path):
    path = au.save(tmp_path / "gen.wav", np.zeros(1600, dtype=np.float32), 16000, ai_generated=True)
    assert au.read_tags(path).get("comment") == AI_GENERATED_TAG


def test_delete_removes_files(voice_wav):
    audio = audio_service.import_file(voice_wav)
    audio_service.delete(audio["audios_id"])
    assert not Path(audio["path"]).exists() and not Path(audio["original_path"]).exists()
