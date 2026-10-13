"""The Library's Files page: every audio VoxLabs keeps, exports wherever they went, and voice samples."""

from pathlib import Path

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.constants.status import Status
from app.exceptions import NotFoundError, ValidationError
from app.models.request import AudioExportRequest, ExportRequest, TTSRequest
from app.services.audio_service import audio_service
from app.services.clone_service import clone_service
from app.services.tts_service import tts_service
from app.utils import audio as au
from app.utils.files import subdir


@pytest.fixture
def client():
    return TestClient(create_app(initialize=False))


def test_every_export_is_recorded_wherever_it_went(voice_wav, tmp_path):
    audio = audio_service.import_file(voice_wav)
    elsewhere = tmp_path / "chosen by the user" / "speech.flac"
    audio_service.export(AudioExportRequest(audios_id=audio["audios_id"], format="flac"), elsewhere)
    audio_service.export(AudioExportRequest(audios_id=audio["audios_id"], format="wav"))  # data/exports
    exports = audio_service.list_exports()
    assert [e["format"] for e in exports] == ["wav", "flac"]  # newest first
    flac = exports[1]
    assert flac["path"] == str(elsewhere.resolve()) and flac["exists"] and flac["audios_id"] == audio["audios_id"]
    assert flac["duration"] == pytest.approx(4.0, abs=0.01) and flac["file_size"] == elsewhere.stat().st_size
    # Exporting to the same file again replaces its entry instead of listing it twice.
    audio_service.export(AudioExportRequest(audios_id=audio["audios_id"], format="flac"), elsewhere)
    assert len(audio_service.list_exports()) == 2


def test_exports_outlive_their_source_and_report_missing_files(voice_wav):
    audio = audio_service.import_file(voice_wav)
    path = Path(audio_service.export(AudioExportRequest(audios_id=audio["audios_id"])))
    audio_service.delete(audio["audios_id"])
    (export,) = audio_service.list_exports()
    assert export["audios_id"] is None and export["exists"]  # the exported file belongs to the user now
    path.unlink()
    assert not audio_service.list_exports()[0]["exists"]


def test_removing_an_export_keeps_or_deletes_the_file(voice_wav):
    audio = audio_service.import_file(voice_wav)
    kept = audio_service.save_export(ExportRequest(audios_id=audio["audios_id"]))
    deleted = audio_service.save_export(ExportRequest(audios_id=audio["audios_id"], format="flac"))
    audio_service.save_export(ExportRequest(exports_id=kept["exports_id"], status=Status.DELETED.code))
    audio_service.save_export(ExportRequest(exports_id=deleted["exports_id"], status=Status.DELETED.code,
                                            delete_file=True))
    assert Path(kept["path"]).exists() and not Path(deleted["path"]).exists()
    assert audio_service.list_exports() == []  # and the kept file in data/exports is not listed again
    with pytest.raises(NotFoundError):
        audio_service.save_export(ExportRequest(exports_id=kept["exports_id"], status=Status.DELETED.code))
    with pytest.raises(ValidationError):
        audio_service.save_export(ExportRequest(exports_id=kept["exports_id"]))


def test_files_already_in_the_exports_folder_are_listed():
    """Exports made before they were recorded are picked up from data/exports."""
    old = subdir("exports") / "old lesson.wav"
    au.save(old, np.zeros(16000, dtype=np.float32), 16000, ai_generated=True)
    (export,) = audio_service.list_exports()
    assert export["name"] == "old lesson" and export["ai_generated"] and export["duration"] == pytest.approx(1.0)


def test_the_library_lists_everything(voice_wav, consent):
    imported = audio_service.import_file(voice_wav)
    generated = tts_service.generate(TTSRequest(text="Library test."))
    audio_service.export(AudioExportRequest(audios_id=generated["audios_id"]))
    voice = clone_service.clone([voice_wav], "Sampled", consent)
    items = audio_service.library()
    kinds = {item["kind"] for item in items}
    assert {"imported", "generated", "export", "sample"} <= kinds
    sample = next(item for item in items if item["kind"] == "sample")
    assert sample["voices_id"] == voice["voices_id"] and sample["name"].startswith("Sampled · ") and sample["exists"]
    assert all(item["exists"] and item["kind_label"] for item in items)
    assert [item["created_at"] for item in items] == sorted((item["created_at"] for item in items), reverse=True)
    assert [item["id"] for item in audio_service.library("imported")] == [imported["audios_id"]]
    gen = next(item for item in audio_service.library("generated") if item["id"] == generated["audios_id"])
    assert gen["original_path"] == generated["original_path"]
    with pytest.raises(ValidationError):
        audio_service.library("everything")


def test_library_and_exports_routes(client, voice_wav):
    audio = audio_service.import_file(voice_wav)
    saved = client.post("/api/exports", json={"audios_id": audio["audios_id"], "format": "wav"}).json()
    assert saved["status"] == 1 and saved["data"]["exists"]
    listed = client.get("/api/exports").json()["data"]
    assert [e["exports_id"] for e in listed] == [saved["data"]["exports_id"]]
    library = client.get("/api/library", params={"kind": "export"}).json()
    assert library["status"] == 1 and [i["id"] for i in library["data"]] == [saved["data"]["exports_id"]]
    removed = client.post("/api/exports", json={"exports_id": saved["data"]["exports_id"],
                                                "status": Status.DELETED.code}).json()
    assert removed["data"]["status"] == Status.DELETED.code
    bad = client.get("/api/library", params={"kind": "nope"}).json()
    assert bad["status"] == 0 and "kind" in bad["error"]["field"]
