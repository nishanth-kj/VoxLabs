import threading

import pytest

from app.constants.status import Status
from app.exceptions import JobError, ValidationError
from app.models.request import TTSRequest
from app.services.job_service import job_service
from app.services.tts_service import tts_service
from app.services.user_service import user_service




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
    user_service.delete_user(user["users_id"])
    assert user_service.list_users() == []
