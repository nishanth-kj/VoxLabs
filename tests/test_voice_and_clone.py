from pathlib import Path

import pytest

from app.constants.consent_status import ConsentStatus
from app.constants.status import Status
from app.exceptions import ConsentError, ValidationError, VoiceError
from app.models import Voice, VoiceConsent
from app.services.clone_service import clone_service
from app.services.consent_service import consent_service
from app.services.voice_service import voice_service
from app.utils.database import read_session
from tests.conftest import make_voice_wav


def test_clone_requires_explicit_consent(voice_wav):
    for bad in (None, {"confirmed": False}, {"confirmed": True, "granted_by": "x"},
                {"confirmed": "yes", "granted_by": "x", "speaker_name": "y"}):
        with pytest.raises(ConsentError):
            clone_service.clone([voice_wav], "Nope", bad)
    with read_session() as session:
        assert session.query(Voice).count() == 0


def test_clone_creates_voice_samples_and_consent(voice_wav, consent):
    voice = clone_service.clone([voice_wav], "Narrator", consent)
    assert voice["source"] == "clone"
    assert voice["sample_count"] == 1
    assert voice["consent_status"] == ConsentStatus.GRANTED.code
    assert voice["consent_status_label"] == "Granted"
    assert voice["pitch_hz"] and 100 < voice["pitch_hz"] < 200
    assert Path(voice["samples"][0]["path"]).exists()
    history = consent_service.history(voice["voices_id"])
    assert history[0]["speaker_name"] == "Test Speaker" and "explicit permission" in history[0]["statement"]


def test_clone_rolls_back_when_samples_too_short(tmp_path, consent):
    short = make_voice_wav(tmp_path / "short.wav", seconds=1.5)
    with pytest.raises(ValidationError):
        clone_service.clone([short], "Too short", consent)
    with read_session() as session:
        assert session.query(Voice).count() == 0
        assert session.query(VoiceConsent).count() == 0
    assert not any((tmp_path / "data" / "voices").glob("*/samples/*.wav"))


def test_multiple_samples_and_sample_management(tmp_path, voice_wav, consent):
    voice = clone_service.clone([voice_wav, make_voice_wav(tmp_path / "b.wav", f0=150)], "Duo", consent)
    assert voice["sample_count"] == 2
    voice = voice_service.attach_sample(voice["voices_id"], make_voice_wav(tmp_path / "c.wav", f0=145))
    assert voice["sample_count"] == 3
    voice = voice_service.remove_sample(voice["samples"][0]["voice_samples_id"])
    assert voice["sample_count"] == 2


def test_revoke_deletes_data_and_blocks_use(voice_wav, consent):
    voice = clone_service.clone([voice_wav], "Revocable", consent)
    sample_path = Path(voice["samples"][0]["path"])
    revoked = voice_service.revoke(voice["voices_id"])
    assert revoked["status"] == Status.INACTIVE.code
    assert revoked["consent_status"] == ConsentStatus.REVOKED.code
    assert not sample_path.exists()
    assert voice_service.list_voices() == []
    with pytest.raises(VoiceError):
        voice_service.validate(voice["voices_id"])
    history = consent_service.history(voice["voices_id"])
    assert history[0]["status"] == Status.INACTIVE.code and history[0]["revoked_at"]


def test_delete_removes_everything(voice_wav, consent):
    voice = clone_service.clone([voice_wav], "Gone", consent)
    storage = Path(voice["samples"][0]["path"]).parents[1]
    voice_service.delete(voice["voices_id"])
    assert not storage.exists()
    with read_session() as session:
        assert session.query(Voice).count() == 0
        assert session.query(VoiceConsent).count() == 0


def test_voice_crud_and_export(voice_wav, consent):
    preset = voice_service.create("Aria", engine_voice="en-US-AriaNeural", model_key="edge-neural")
    assert preset["source"] == "preset"
    renamed = voice_service.rename(preset["voices_id"], "Aria (Edge)")
    assert renamed["name"] == "Aria (Edge)"
    cloned = clone_service.clone([voice_wav], "Cloned", consent)
    meta = voice_service.export_metadata(cloned["voices_id"])
    assert meta["consents"] and "path" not in meta["samples"][0]
    with pytest.raises(VoiceError):
        voice_service.update(cloned["voices_id"], status=1)
