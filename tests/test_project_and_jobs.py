import threading
import zipfile
from pathlib import Path

import pytest

from app.constants.status import Status
from app.exceptions import JobError, NotFoundError, ValidationError
from app.models.request import TTSRequest
from app.services.job_service import job_service
from app.services.project_service import project_service
from app.services.script_service import script_service
from app.services.tts_service import tts_service
from app.services.user_service import user_service


def test_project_lifecycle(tmp_path):
    project = project_service.create_project("Course", "lesson")
    script = script_service.create("Lesson 1", "Intro text here.", projects_id=project["projects_id"])
    script_service.generate(script["scripts_id"])
    opened = project_service.open_project(project["projects_id"])
    assert len(opened["scripts"]) == 1 and opened["takes"] == 1 and opened["audios"]

    project_service.save_project(project["projects_id"], edit_state={"zoom": 2})
    assert project_service.get(project["projects_id"])["edit_state"] == {"zoom": 2}
    assert project_service.rename_project(project["projects_id"], "Course v2")["name"] == "Course v2"

    copy = project_service.duplicate_project(project["projects_id"])
    copied = project_service.open_project(copy["projects_id"])
    assert copied["takes"] == 1 and len(copied["audios"]) == len(opened["audios"])
    assert {a["path"] for a in copied["audios"]}.isdisjoint({a["path"] for a in opened["audios"]})

    archive = project_service.export_project(project["projects_id"], tmp_path / "course.zip")
    with zipfile.ZipFile(archive) as zf:
        assert "project.json" in zf.namelist() and any(n.startswith("audio/") for n in zf.namelist())

    paths = [a["path"] for a in opened["audios"]]
    project_service.delete_project(project["projects_id"])
    assert not any(Path(p).exists() for p in paths)
    with pytest.raises(NotFoundError):
        project_service.get(project["projects_id"])
    with pytest.raises(ValidationError):
        project_service.create_project("Bad", "movie")


def test_job_lifecycle_and_failure():
    job = job_service.submit("test", lambda ctx: (ctx.progress(0.5), {"value": 42})[1])
    done = job_service.wait(job["jobs_id"], timeout=10)
    assert done["status"] == Status.COMPLETED.code and done["result"]["value"] == 42 and done["progress"] == 1.0

    def boom(_ctx):
        raise ValidationError("bad input")

    failed = job_service.wait(job_service.submit("test", boom)["jobs_id"], timeout=10)
    assert failed["status"] == Status.FAILED.code and failed["error"] == "bad input"
    with pytest.raises(JobError):
        job_service.cancel(done["jobs_id"])


def test_job_cancellation_and_listeners():
    events = []
    job_service.add_listener(lambda job: events.append(job["status_label"]))
    started, release = threading.Event(), threading.Event()

    def slow(ctx):
        started.set()
        release.wait(5)
        ctx.progress(0.9)  # raises JobCancelled once cancel() was requested
        return {}

    job = job_service.submit("test", slow)
    started.wait(5)
    job_service.cancel(job["jobs_id"])
    release.set()
    final = job_service.wait(job["jobs_id"], timeout=10)
    assert final["status"] == Status.CANCELLED.code
    assert "InProgress" in events and "Cancelled" in events


def test_async_tts_job():
    job = tts_service.generate_async(TTSRequest(text="Background speech."))
    result = job_service.wait(job["jobs_id"], timeout=30)
    assert result["status"] == Status.COMPLETED.code and result["result"]["audio"]["ai_generated"]


def test_users():
    user = user_service.create_user("Ada", "ada@example.com")
    assert user_service.get_user(user["users_id"])["email"] == "ada@example.com"
    with pytest.raises(ValidationError):
        user_service.create_user("Dup", "ada@example.com")
    with pytest.raises(ValidationError):
        user_service.create_user("Bad", "not-an-email")
    project_service.create_project("Mine", users_id=user["users_id"])
    assert len(user_service.get_user_projects(user["users_id"])) == 1
    user_service.delete_user(user["users_id"])
    assert user_service.list_users() == []
