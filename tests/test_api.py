import pytest
from fastapi.testclient import TestClient

from app.api.app import create_app
from app.constants.status import Status
from app.services.job_service import job_service
from app.services.system_service import system_service


@pytest.fixture
def client():
    # Services are initialized by the autouse fixture; skip the lifespan re-init.
    return TestClient(create_app(initialize=False))


def ok(response) -> dict:
    """Every API response is HTTP 200; success is status 1 in the envelope."""
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == 1 and body["error"] is None, body
    return body["data"]


def failed(response) -> dict:
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == 0 and body["data"] is None, body
    return body["error"]


def test_health_envelope(client):
    assert ok(client.get("/api/health"))["status"] == "ok"


def test_errors_use_envelope_with_http_200(client):
    assert failed(client.get("/api/voices/999")) == {
        "error_code": 404, "error_message": "The requested item was not found.",
        "field": {"voices_id": "Voice 999 not found"}}
    invalid = failed(client.post("/api/tts", json={"text": "hi", "speed": 9}))
    assert invalid["error_code"] == 422
    assert invalid["field"] == {"speed": "speed must be between 0.5 and 2.0"}
    missing_field = failed(client.post("/api/tts", json={}))
    assert missing_field["error_message"] == "Some input values are invalid." and "text" in missing_field["field"]
    assert failed(client.get("/api/nope"))["error_code"] == 404


def test_users_single_save_endpoint(client):
    user = ok(client.post("/api/users", json={"name": "Ada", "email": "ada@example.com"}))
    users_id = user["users_id"]
    updated = ok(client.post("/api/users", json={"users_id": users_id, "name": "Ada L."}))
    assert updated["name"] == "Ada L." and updated["email"] == "ada@example.com"
    deleted = ok(client.post("/api/users", json={"users_id": users_id, "status": Status.DELETED.code}))
    assert deleted == {"users_id": users_id, "status": Status.DELETED.code, "status_label": "Deleted"}
    assert ok(client.get("/api/users")) == []


def test_tts_and_audio_routes(client):
    audio = ok(client.post("/api/tts", json={"text": "Hello from the API."}))
    assert ok(client.get(f"/api/audio/{audio['audios_id']}"))["ai_generated"] is True
    ok(client.post("/api/audio/process", json={"audios_id": audio["audios_id"], "preset": "Narration"}))
    again = ok(client.post("/api/tts/regenerate", json={"audios_id": audio["audios_id"], "seed": 3}))
    assert again["params"]["seed"] == 3
    exported = client.post("/api/audio/export", json={"audios_id": audio["audios_id"], "format": "flac"})
    assert exported.status_code == 200 and exported.content[:4] == b"fLaC"


def test_background_job_route(client):
    job = ok(client.post("/api/tts", json={"text": "Queued speech.", "background": True}))["job"]
    job_service.wait(job["jobs_id"], timeout=30)
    assert ok(client.get(f"/api/jobs/{job['jobs_id']}"))["status_label"] == "Completed"


def test_clone_route_requires_consent_and_voice_save(client, voice_wav):
    form = {"name": "API voice", "consent": "false", "granted_by": "me", "speaker_name": "me"}
    with open(voice_wav, "rb") as fh:
        refused = failed(client.post("/api/voices/clone", data=form, files={"samples": ("s.wav", fh, "audio/wav")}))
    assert refused["error_code"] == 403
    with open(voice_wav, "rb") as fh:
        form["consent"] = "true"
        voice = ok(client.post("/api/voices/clone", data=form, files={"samples": ("s.wav", fh, "audio/wav")}))
    voices_id = voice["voices_id"]
    assert ok(client.post("/api/voices", json={"voices_id": voices_id, "name": "Renamed"}))["name"] == "Renamed"
    ok(client.post("/api/voices", json={"voices_id": voices_id, "status": Status.DELETED.code}))
    assert failed(client.get(f"/api/voices/{voices_id}"))["error_code"] == 404
    preset = ok(client.post("/api/voices", json={"name": "Aria", "engine_voice": "en-US-AriaNeural"}))
    assert preset["source"] == "preset"


def test_scripts_projects_models(client):
    project = ok(client.post("/api/projects", json={"name": "P", "project_type": "lesson"}))
    script = ok(client.post("/api/scripts", json={"title": "S", "body": "Teacher: Hi.\n\nStudent: Hello.",
                                                  "projects_id": project["projects_id"]}))
    assert script["speakers"] == ["Teacher", "Student"]
    section_id = script["sections"][0]["script_sections_id"]
    assert ok(client.post("/api/scripts/sections", json={"script_sections_id": section_id, "speed": 1.1}))["speed"] == 1.1
    result = ok(client.post(f"/api/scripts/{script['scripts_id']}/generate", json={"background": False}))
    assert result["audio"]["source"] == "rendered"
    assert ok(client.get(f"/api/projects/{project['projects_id']}"))["takes"] == 2
    renamed = ok(client.post("/api/projects", json={"projects_id": project["projects_id"], "name": "P2"}))
    assert renamed["name"] == "P2"
    ok(client.post("/api/scripts", json={"scripts_id": script["scripts_id"], "status": Status.DELETED.code}))
    ok(client.post("/api/projects", json={"projects_id": project["projects_id"], "status": Status.DELETED.code}))
    assert ok(client.get("/api/projects")) == []

    models = ok(client.get("/api/models"))
    assert any(m["key"] == "piper-en-us-lessac-medium" for m in models)
    assert ok(client.post("/api/models/fake-tts/load"))["loaded"] is True
    assert ok(client.post("/api/models/fake-tts/unload"))["loaded"] is False


def test_optional_token_auth(client):
    system_service.update_settings(api_token="secret")
    ok(client.get("/api/health"))
    assert failed(client.get("/api/voices"))["error_code"] == 401
    ok(client.get("/api/voices", headers={"Authorization": "Bearer secret"}))
