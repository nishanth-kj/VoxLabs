"""Tests for the complete Video Dubbing workflow: subtitles, models, service, conflict detection and API."""

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.api.app import app
from app.constants.status import Status
from app.models.dubbing import DubbingProject, DubbingSegment
from app.models.request import (
    DubbingImportRequest,
    DubbingProjectRequest,
    DubbingRenderRequest,
    DubbingSegmentRequest,
)
from app.services.dubbing_service import (
    compute_segment_metrics,
    dubbing_service,
    duck_and_mix,
)
from app.utils.subtitles import (
    extract_speaker_and_text,
    ms_to_timestamp,
    parse_srt,
    parse_subtitles,
    parse_vtt,
    timestamp_to_ms,
    to_srt,
    to_vtt,
)

SAMPLE_SRT = """1
00:00:01,000 --> 00:00:04,500
[Narrator]: Welcome to the local AI production studio.

2
00:00:05,200 --> 00:00:08,000
Alice: How does speech synthesis work?

3
00:00:08,500 --> 00:00:12,100
Bob: It translates text into neural audio waveforms.
"""

SAMPLE_VTT = """WEBVTT

00:00:01.000 --> 00:00:04.500
<v Narrator>Welcome to the local AI production studio.

00:00:05.200 --> 00:00:08.000
<v Alice>How does speech synthesis work?

00:00:08.500 --> 00:00:12.100
<v Bob>It translates text into neural audio waveforms.
"""


def test_subtitles_parsing_and_formatting():
    # Test timestamps
    assert ms_to_timestamp(1500, separator=",") == "00:00:01,500"
    assert ms_to_timestamp(3661234, separator=".") == "01:01:01.234"
    assert timestamp_to_ms(0, 1, 23, 456) == 83456

    # Test speaker extraction
    speaker, text = extract_speaker_and_text("[Instructor]: Test dialogue")
    assert speaker == "Instructor"
    assert text == "Test dialogue"

    speaker, text = extract_speaker_and_text("<v Host>Welcome everyone</v>")
    assert speaker == "Host"
    assert text == "Welcome everyone"

    # Test SRT parsing
    srt_segments = parse_srt(SAMPLE_SRT)
    assert len(srt_segments) == 3
    assert srt_segments[0]["speaker"] == "Narrator"
    assert srt_segments[0]["start_ms"] == 1000
    assert srt_segments[0]["end_ms"] == 4500
    assert srt_segments[1]["speaker"] == "Alice"

    # Test VTT parsing
    vtt_segments = parse_vtt(SAMPLE_VTT)
    assert len(vtt_segments) == 3
    assert vtt_segments[0]["speaker"] == "Narrator"
    assert vtt_segments[2]["speaker"] == "Bob"

    # Test roundtrip formatting
    srt_out = to_srt(srt_segments)
    assert "00:00:01,000 --> 00:00:04,500" in srt_out
    assert "Alice" in srt_out

    vtt_out = to_vtt(vtt_segments)
    assert "WEBVTT" in vtt_out
    assert "00:00:01.000 --> 00:00:04.500" in vtt_out


def test_conflict_detection_metrics():
    # No audio generated yet
    seg_none = {"start_ms": 1000, "end_ms": 4000, "generated_duration_ms": None}
    metrics = compute_segment_metrics(seg_none)
    assert metrics["slot_duration_ms"] == 3000
    assert metrics["conflict_type"] == "none"

    # Synchronized within tolerance
    seg_ok = {"start_ms": 1000, "end_ms": 4000, "generated_duration_ms": 3050}
    metrics = compute_segment_metrics(seg_ok)
    assert metrics["conflict_type"] == "ok"
    assert metrics["delta_ms"] == 50

    # Overflow (longer than slot by > 100ms)
    seg_over = {"start_ms": 1000, "end_ms": 4000, "generated_duration_ms": 3600}
    metrics = compute_segment_metrics(seg_over)
    assert metrics["conflict_type"] == "overflow"
    assert metrics["delta_ms"] == 600

    # Underflow (shorter than slot by > 300ms)
    seg_under = {"start_ms": 1000, "end_ms": 4000, "generated_duration_ms": 2200}
    metrics = compute_segment_metrics(seg_under)
    assert metrics["conflict_type"] == "underflow"
    assert metrics["delta_ms"] == -800


def test_duck_and_mix():
    sr = 22050
    duration_s = 2.0
    num_samples = int(duration_s * sr)

    # Background audio: continuous 0.4 amplitude tone
    bg = np.ones(num_samples, dtype=np.float32) * 0.4
    # Foreground dialogue: burst of 0.6 amplitude in the middle (0.5s to 1.5s)
    fg = np.zeros(num_samples, dtype=np.float32)
    fg[int(0.5 * sr) : int(1.5 * sr)] = 0.6

    mixed = duck_and_mix(bg, fg, sr, duck_volume=0.2)
    assert len(mixed) >= num_samples
    assert np.all(np.isfinite(mixed))
    # Before dialogue starts, background should be preserved (~0.4)
    assert mixed[int(0.1 * sr)] > 0.3
    # During dialogue, background is ducked and combined cleanly without clipping
    assert np.max(np.abs(mixed)) <= 1.0


def test_dubbing_service_crud_and_subtitles(tmp_path):
    # Create a dummy media file
    media_file = tmp_path / "sample_video.mp4"
    media_file.write_bytes(b"dummy video data")

    # Create project
    req = DubbingProjectRequest(
        title="Test Dubbing Project",
        source_media_path=str(media_file),
        source_language="en",
        target_language="es",
    )
    project = dubbing_service.save(req)
    proj_id = project["dubbing_projects_id"]
    assert project["title"] == "Test Dubbing Project"
    assert project["target_language"] == "es"

    # Import subtitles
    sub_res = dubbing_service.import_subtitles(
        dubbing_projects_id=proj_id,
        content=SAMPLE_SRT,
        format="srt",
    )
    assert len(sub_res["segments"]) == 3
    assert sub_res["speakers"] == ["Narrator", "Alice", "Bob"]

    # Export subtitles
    exported_srt = dubbing_service.export_subtitles(proj_id, format="srt")
    assert "Alice" in exported_srt

    # Save segment edit
    seg0 = sub_res["segments"][0]
    seg_edit = DubbingSegmentRequest(
        dubbing_segments_id=seg0["dubbing_segments_id"],
        target_text="Bienvenido al estudio de producción de IA.",
        speed=1.05,
        locked=True,
    )
    updated_seg = dubbing_service.save_segment(seg_edit)
    assert updated_seg["target_text"] == "Bienvenido al estudio de producción de IA."
    assert updated_seg["speed"] == 1.05
    assert updated_seg["locked"] is True

    # Auto map speakers
    mapped = dubbing_service.auto_map_speakers(proj_id)
    assert isinstance(mapped["speaker_map"], dict)

    # Delete project
    del_res = dubbing_service.save(DubbingProjectRequest(dubbing_projects_id=proj_id, status=Status.DELETED.code))
    assert del_res["status"] == Status.DELETED.code


def test_dubbing_rest_api(tmp_path):
    client = TestClient(app)
    media_file = tmp_path / "api_test_video.mp4"
    media_file.write_bytes(b"dummy video data")

    # POST create
    res = client.post("/api/dubbing", json={
        "title": "API Dubbing Project",
        "source_media_path": str(media_file),
    })
    assert res.status_code == 200
    data = res.json()["data"]
    proj_id = data["dubbing_projects_id"]
    assert data["title"] == "API Dubbing Project"

    # GET list
    list_res = client.get("/api/dubbing")
    assert list_res.status_code == 200
    assert any(p["dubbing_projects_id"] == proj_id for p in list_res.json()["data"])

    # POST import subtitles
    sub_res = client.post("/api/dubbing/import-subtitles", json={
        "dubbing_projects_id": proj_id,
        "content": SAMPLE_SRT,
        "format": "srt",
    })
    assert sub_res.status_code == 200
    assert len(sub_res.json()["data"]["segments"]) == 3

    # GET export subtitles
    exp_res = client.get(f"/api/dubbing/{proj_id}/subtitles?format=srt")
    assert exp_res.status_code == 200
    assert "Alice" in exp_res.json()["data"]

    # DELETE project
    del_res = client.post("/api/dubbing", json={
        "dubbing_projects_id": proj_id,
        "status": Status.DELETED.code,
    })
    assert del_res.status_code == 200
    assert del_res.json()["data"]["status"] == Status.DELETED.code

