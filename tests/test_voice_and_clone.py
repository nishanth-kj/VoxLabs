from pathlib import Path

import pytest

from app.constants.consent_status import ConsentStatus
from app.constants.status import Status
from app.exceptions import ConsentError, ValidationError, VoiceError
from app.models import Voice, VoiceConsent
from app.services.clone_service import clone_service
from app.services.consent_service import consent_service
from app.services.system_service import system_service
from app.services.voice_service import voice_service
from app.utils.database import read_session
from tests.conftest import make_voice_wav


def test_clone_requires_explicit_consent(voice_wav):
    for bad in (None, {"confirmed": False}, {"confirmed": True, "granted_by": "x"},
                {"confirmed": "yes", "granted_by": "x", "speaker_name": "y"}):
        with pytest.raises(ConsentError):
            clone_service.clone([voice_wav], "Nope", bad)
    with read_session() as session:
        assert session.query(Voice).filter(Voice.source == "clone").count() == 0


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
        assert session.query(Voice).filter(Voice.source == "clone").count() == 0
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
    assert voice["voices_id"] not in {item["voices_id"] for item in voice_service.list_voices()}
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
        assert session.get(Voice, voice["voices_id"]) is None
        assert session.query(VoiceConsent).count() == 0


def test_voice_search_filters_by_model_and_hides_edge_when_off():
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from app.ui.widgets.voice_selector import voice_matches

    kokoro = {"name": "Kokoro · Heart", "engine_voice": "af_heart", "language": "en",
              "model_key": "kokoro-82m", "description": "", "source": "preset"}
    edge = {"name": "Edge · Aria", "engine_voice": "en-US-AriaNeural", "language": "en",
            "model_key": "edge-neural", "description": "", "source": "preset"}
    assert voice_matches(kokoro, "heart", "kokoro-82m", allow_edge=False)
    assert not voice_matches(kokoro, "heart", "edge-neural", allow_edge=False)
    assert not voice_matches(edge, "", None, allow_edge=False)
    assert voice_matches(edge, "aria", "edge-neural", allow_edge=True)


def test_builtin_voices_cover_kokoro_edge_and_piper():
    voices = voice_service.list_voices()
    kokoro = [voice for voice in voices if voice["model_key"] == "kokoro-82m"]
    edge = [voice for voice in voices if voice["model_key"] == "edge-neural"]
    piper = [voice for voice in voices if voice["name"].startswith("Piper · Lessac")]
    assert len(kokoro) == 54
    assert len(edge) == 322
    assert len(piper) == 1
    assert all(len(voice["name"]) <= 120 for voice in voices)
    assert {voice["engine_voice"] for voice in kokoro} >= {"af_heart", "af_bella", "bm_george"}
    assert "en-US-AriaNeural" in {voice["engine_voice"] for voice in edge}
    assert system_service.get_setting("default_voices_id") == piper[0]["voices_id"]
    assert voice_service.ensure_builtin_voices() == 0


def test_clone_models_have_built_in_voices():
    voices = voice_service.list_voices()
    qwen = {voice["engine_voice"] for voice in voices if voice["model_key"] == "qwen3-tts-0.6b"}
    assert qwen == {"ryan", "aiden", "vivian", "serena", "uncle_fu", "dylan", "eric", "ono_anna", "sohee"}
    for key in ("chatterbox", "chatterbox-turbo"):
        own = [voice for voice in voices if voice["model_key"] == key]
        assert len(own) == 1 and own[0]["engine_voice"] is None and own[0]["source"] == "preset"


def test_new_voice_packs_reach_older_databases():
    """A database from before packs were tracked gets only the new packs, once; deleted presets stay deleted."""
    from app.constants.status import Status
    from app.models import Voice
    from app.utils.database import transaction

    with transaction() as session:
        for voice in session.query(Voice).filter(Voice.model_key.in_(("chatterbox", "chatterbox-turbo",
                                                                     "qwen3-tts-0.6b"))):
            session.delete(voice)
    system_service.update_settings(builtin_voices_seeded=True, builtin_voice_packs=[])
    assert voice_service.ensure_builtin_voices() == 11  # 2 Chatterbox + 9 Qwen3-TTS, no Kokoro/Edge repeats
    ryan = next(v for v in voice_service.list_voices() if v["engine_voice"] == "ryan")
    with transaction() as session:
        row = session.get(Voice, ryan["voices_id"])
        assert row is not None
        row.status = Status.DELETED.code
    assert voice_service.ensure_builtin_voices() == 0
    assert "ryan" not in {voice["engine_voice"] for voice in voice_service.list_voices()}


def test_voice_editor_delivery_is_saved(voice_wav, consent):
    voice = voice_service.create("Narrator", model_key="fake-tts")
    saved = voice_service.update(voice["voices_id"], delivery={
        "speed": 0.8, "pitch": 1.1, "energy": 0.9, "emotion": "calm", "style": "lecture",
    }, model_key="fake-tts")
    assert saved["delivery"]["speed"] == 0.8
    assert saved["delivery"]["emotion"] == "calm"
    assert saved["delivery"]["style"] == "lecture"
    again = voice_service.get(saved["voices_id"], with_samples=False)
    assert again["model_key"] == "fake-tts"
    assert again["delivery"]["pitch"] == 1.1
    filled = voice_service.apply_delivery(again, {"speed": None, "emotion": None})
    assert filled["speed"] == 0.8 and filled["emotion"] == "calm"
    # An explicit section setting still wins over the voice editor.
    assert voice_service.apply_delivery(again, {"speed": 1.4})["speed"] == 1.4


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
