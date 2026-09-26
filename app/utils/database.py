"""SQLite + SQLAlchemy infrastructure: engine, Base, sessions and transactions.

Base is a plain declarative base. Every model declares its own
`<table_name>_id` primary key, INTEGER `status` (a `Status` code, e.g.
`default=Status.ACTIVE.code`), `created_at` and `updated_at` columns
explicitly. Services own transaction boundaries via `transaction()`; models
never commit on their own.
"""

import json
import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.constants.status import Status
from app.utils.files import subdir
from app.utils.logger import logger
from app.utils.time import iso


class Base(DeclarativeBase):
    pass


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def database_path() -> Path:
    override = os.getenv("VOXLABS_DB_PATH")
    return Path(override) if override else subdir("database") / "voxlabs.db"


def _set_sqlite_pragmas(dbapi_connection, _record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.close()


def get_engine() -> Engine:
    global _engine, _session_factory
    if _engine is None:
        _engine = create_engine(
            f"sqlite:///{database_path()}",
            connect_args={"check_same_thread": False, "timeout": 30},
        )
        event.listen(_engine, "connect", _set_sqlite_pragmas)
        _session_factory = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def reset_engine() -> None:
    """Drop the cached engine (tests switch data directories between runs)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def init_db() -> None:
    import app.models  # noqa: F401 - registers every table on Base.metadata

    engine = get_engine()
    Base.metadata.create_all(engine)
    _upgrade(engine)
    logger.info(f"Database ready: {database_path()}")


def _upgrade(engine: Engine) -> None:
    """In-place upgrades for databases from earlier 3.0 builds (`create_all` never alters a table)."""
    if "edit_ops" not in {column["name"] for column in inspect(engine).get_columns("audios")}:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE audios ADD COLUMN edit_ops JSON DEFAULT '[]'"))
            # Editor ops used to live in projects.edit_state["editor"][<audios_id>], so audio
            # without a project never kept its edits. Move them onto the audio.
            for projects_id, raw in conn.execute(text("SELECT projects_id, edit_state FROM projects")).all():
                state = json.loads(raw) if raw else {}
                editor = state.pop("editor", None) if isinstance(state, dict) else None
                if not editor:
                    continue
                for audios_id, ops in editor.items():
                    conn.execute(text("UPDATE audios SET edit_ops = :ops WHERE audios_id = :id"),
                                 {"ops": json.dumps(ops), "id": int(audios_id)})
                conn.execute(text("UPDATE projects SET edit_state = :state WHERE projects_id = :id"),
                             {"state": json.dumps(state), "id": projects_id})
        logger.info("Database upgraded: audios.edit_ops")


def new_session() -> Session:
    get_engine()
    assert _session_factory is not None
    return _session_factory()


@contextmanager
def transaction() -> Iterator[Session]:
    """Unit of work: commits on success, rolls everything back on error."""
    session = new_session()
    try:
        yield session
        session.commit()
    except Exception as exc:
        session.rollback()
        logger.debug(f"Transaction rolled back: {exc!r}")
        raise
    finally:
        session.close()


def serialize(row: Base, exclude: tuple[str, ...] = ()) -> dict:
    """Column values as a plain dict.

    Datetimes become ISO-8601 UTC strings. The integer `status` gets a readable
    `status_label` next to it (e.g. status=4, status_label="InProgress").
    """
    data = {}
    for column in row.__table__.columns:
        if column.key in exclude:
            continue
        value = getattr(row, column.key)
        if isinstance(value, datetime):
            value = iso(value)
        data[column.key] = value
    if "status" in data:
        data["status_label"] = Status.label(data["status"])
    return data


def deleted_result(pk_name: str, pk: int) -> dict:
    """What a `save()` call returns after deleting a row."""
    return {pk_name: pk, "status": Status.DELETED.code, "status_label": Status.DELETED.value}


@contextmanager
def read_session() -> Iterator[Session]:
    session = new_session()
    try:
        yield session
    finally:
        session.close()
