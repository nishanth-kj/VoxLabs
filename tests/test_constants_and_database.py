import pytest
from sqlalchemy import inspect

from app.constants.base_enum import BaseEnum
from app.constants.consent_status import ConsentStatus
from app.constants.status import Status
from app.models import User
from app.utils.database import Base, get_engine, read_session, transaction


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
        created = session.get(User, users_id).updated_at
    with transaction() as session:
        session.get(User, users_id).name = "Ada L."
    with read_session() as session:
        user = session.get(User, users_id)
        assert user.status == Status.ACTIVE.code
        assert user.updated_at >= created
        assert user.created_at is not None
