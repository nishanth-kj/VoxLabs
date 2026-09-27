import json

import pytest
from sqlalchemy import JSON, Column, ForeignKey, Integer, MetaData, String, Table, inspect, text
from sqlalchemy.schema import CreateTable

from app.constants.base_enum import BaseEnum
from app.constants.consent_status import ConsentStatus
from app.constants.status import Status
from app.models import User
from app.models.request import TTSRequest
from app.services.audio_service import audio_service
from app.services.script_service import script_service
from app.services.tts_service import tts_service
from app.utils.database import Base, database_path, get_engine, init_db, read_session, transaction


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
    expected = {"users", "voices", "voice_samples", "voice_consents", "audios", "scripts",
                "script_sections", "takes", "jobs", "models"}
    assert expected <= set(inspector.get_table_names()) and "projects" not in inspector.get_table_names()
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


def _to_old_shape(engine) -> None:
    """Rebuild audios and scripts as earlier builds wrote them: a projects_id column whose foreign key is a
    table-level FOREIGN KEY constraint (how SQLAlchemy writes it, and what stops SQLite dropping the column),
    its index, a projects table, and no audios.edit_ops."""
    copies = MetaData()
    for table in Base.metadata.sorted_tables:
        table.to_metadata(copies)
    projects = Table("projects", copies, Column("projects_id", Integer, primary_key=True),
                     Column("name", String(255)), Column("edit_state", JSON))
    raw = engine.raw_connection()
    try:
        db = raw.driver_connection
        db.isolation_level = None
        cursor = db.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute(str(CreateTable(projects).compile(dialect=engine.dialect)))
        for name, on_delete in (("audios", "SET NULL"), ("scripts", "CASCADE")):
            old = Base.metadata.tables[name].to_metadata(copies, name=f"{name}__old")
            old.append_column(Column("projects_id", Integer, ForeignKey("projects.projects_id", ondelete=on_delete)))
            columns = ", ".join(column.name for column in Base.metadata.tables[name].columns)
            cursor.execute(str(CreateTable(old).compile(dialect=engine.dialect)))
            cursor.execute(f"INSERT INTO {name}__old ({columns}) SELECT {columns} FROM {name}")
            cursor.execute(f"DROP TABLE {name}")
            cursor.execute(f"ALTER TABLE {name}__old RENAME TO {name}")
            cursor.execute(f"CREATE INDEX ix_{name}_projects_id ON {name} (projects_id)")
        cursor.execute("ALTER TABLE audios DROP COLUMN edit_ops")
        cursor.execute("PRAGMA foreign_keys = ON")
    finally:
        raw.close()


def test_upgrade_moves_editor_ops_and_drops_projects():
    """A database from an earlier 3.0 build: no audios.edit_ops, and a projects table that audio and scripts
    belonged to (scripts ON DELETE CASCADE, sections cascading from scripts). init_db moves the editor ops
    onto the audio, rebuilds audios and scripts without projects_id, drops projects, keeps every row and
    leaves a backup."""
    audio = tts_service.generate(TTSRequest(text="Legacy edits."))
    script = script_service.create("Lesson", "Hello there.\n\nSecond part.")
    sections = len(script_service.get(script["scripts_id"])["sections"])
    ops = [{"op": "delete", "start": 0, "end": 0.2}]
    engine = get_engine()
    _to_old_shape(engine)
    with engine.begin() as conn:
        assert "FOREIGN KEY(projects_id)" in conn.execute(  # the real old schema, not a simpler one
            text("SELECT sql FROM sqlite_master WHERE name = 'audios'")).scalar_one()
        conn.execute(text("INSERT INTO projects VALUES (1, 'Old', :state)"),
                     {"state": json.dumps({"zoom": 2, "editor": {str(audio["audios_id"]): ops}})})
        conn.execute(text("UPDATE audios SET projects_id = 1"))
        conn.execute(text("UPDATE scripts SET projects_id = 1"))

    init_db()
    inspector = inspect(get_engine())
    assert "projects" not in inspector.get_table_names()
    for table in ("audios", "scripts"):
        assert "projects_id" not in {column["name"] for column in inspector.get_columns(table)}
    assert audio_service.get(audio["audios_id"])["edit_ops"] == ops
    kept = script_service.get(script["scripts_id"])  # not cascaded away with the project
    assert kept["title"] == "Lesson" and len(kept["sections"]) == sections
    with get_engine().connect() as conn:
        assert conn.execute(text("PRAGMA integrity_check")).scalar_one() == "ok"
        assert conn.execute(text("PRAGMA foreign_key_check")).fetchall() == []
    assert database_path().with_name("voxlabs-before-projects-removal.db").exists()
    init_db()  # idempotent
