import json

import pytest
from sqlalchemy import inspect, text

from app.constants.base_enum import BaseEnum
from app.constants.consent_status import ConsentStatus
from app.constants.status import Status
from app.models import User
from app.models.request import TTSRequest
from app.services.audio_service import audio_service
from app.services.project_service import project_service
from app.services.tts_service import tts_service
from app.utils.database import Base, get_engine, init_db, read_session, transaction


def test_base_enum_code_and_value():
    assert Status.IN_PROGRESS.code == 4
    assert Status.IN_PROGRESS.value == "InProgress"
    assert Status(4) is Status.IN_PROGRESS
    assert Status.label(5) == "Completed"
    assert issubclass(Status, BaseEnum) and issubclass(ConsentStatus, BaseEnum)
    assert len({s.code for s in Status}) == len(Status)
    assert ConsentStatus.REVOKED.value == "Revoked"


def test_status_column_stores_integer_code():
    with transaction() as session:
        session.add(User(name="Coded", status=Status.INACTIVE.code))
    with get_engine().connect() as conn:
        raw = conn.exec_driver_sql("SELECT status, typeof(status) FROM users").one()
    assert tuple(raw) == (2, "integer")
    with read_session() as session:
        assert session.query(User).one().status == Status.INACTIVE.code


def test_every_table_follows_naming_convention():
    inspector = inspect(get_engine())
    expected = {"users", "voices", "voice_samples", "voice_consents", "audios", "projects", "scripts",
                "script_sections", "takes", "jobs", "models"}
    assert expected <= set(inspector.get_table_names())
    for table in Base.metadata.tables.values():
        columns = {c.name: c for c in table.columns}
        pk = f"{table.name}_id"
        assert pk in columns and columns[pk].primary_key, table.name
        assert "id" not in columns
        for required in ("status", "created_at", "updated_at"):
            assert required in columns, f"{table.name}.{required}"


def test_transaction_commits_and_rolls_back():
    with transaction() as session:
        session.add(User(name="Kept"))
    with pytest.raises(RuntimeError):
        with transaction() as session:
            session.add(User(name="Rolled back"))
            session.flush()
            raise RuntimeError("boom")
    with read_session() as session:
        names = [u.name for u in session.query(User)]
    assert names == ["Kept"]


def test_timestamps_are_set_and_updated():
    with transaction() as session:
        user = User(name="Ada")
        session.add(user)
        session.flush()
        users_id = user.users_id
    with read_session() as session:
        user = session.get(User, users_id)
        assert user is not None
        created = user.updated_at
    with transaction() as session:
        user = session.get(User, users_id)
        assert user is not None
        user.name = "Ada L."
    with read_session() as session:
        user = session.get(User, users_id)
        assert user is not None
        assert user.status == Status.ACTIVE.code
        assert user.updated_at >= created
        assert user.created_at is not None


def test_upgrade_moves_editor_ops_from_project_onto_audio():
    """A database from an earlier 3.0 build has no audios.edit_ops; init_db adds it and moves project ops."""
    project = project_service.create_project("Old")
    audio = tts_service.generate(TTSRequest(text="Legacy edits.", projects_id=project["projects_id"]))
    ops = [{"op": "delete", "start": 0, "end": 0.2}]
    with get_engine().begin() as conn:
        conn.execute(text("ALTER TABLE audios DROP COLUMN edit_ops"))
        conn.execute(text("UPDATE projects SET edit_state = :state"),
                     {"state": json.dumps({"zoom": 2, "editor": {str(audio["audios_id"]): ops}})})
    init_db()
    assert audio_service.get(audio["audios_id"])["edit_ops"] == ops
    assert project_service.get(project["projects_id"])["edit_state"] == {"zoom": 2}
    init_db()  # idempotent
