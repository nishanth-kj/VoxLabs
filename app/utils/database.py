"""SQLite + SQLAlchemy infrastructure: engine, Base, sessions and transactions.

Base is a plain declarative base. Every model declares its own
`<table_name>_id` primary key, INTEGER `status` (a `Status` code, e.g.
`default=Status.ACTIVE.code`), `created_at` and `updated_at` columns
explicitly. Services own transaction boundaries via `transaction()`; models
never commit on their own.
"""

import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, event
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

    Base.metadata.create_all(get_engine())
    logger.info(f"Database ready: {database_path()}")


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
