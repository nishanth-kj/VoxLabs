"""SQLite + SQLAlchemy infrastructure: engine, Base, sessions and transactions.

Base is a plain declarative base. Every model declares its own
`<table_name>_id` primary key, INTEGER `status` (a `Status` code, e.g.
`default=Status.ACTIVE.code`), `created_at` and `updated_at` columns
explicitly. Services own transaction boundaries via `transaction()`; models
never commit on their own.
"""

import json
import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import cast

from sqlalchemy import MetaData, create_engine, event, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.schema import CreateIndex, CreateTable

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
            conn.execute(text("ALTER TABLE audios ADD COLUMN edit_ops JSON NOT NULL DEFAULT '[]'"))
            # Editor ops used to live in projects.edit_state["editor"][<audios_id>], so audio
            # without a project never kept its edits. Move them onto the audio.
            has_projects = "projects" in inspect(conn).get_table_names()
            rows = conn.execute(text("SELECT projects_id, edit_state FROM projects")).all() if has_projects else []
            for projects_id, raw in rows:
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
    if "delivery" not in {column["name"] for column in inspect(engine).get_columns("voices")}:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE voices ADD COLUMN delivery JSON NOT NULL DEFAULT '{}'"))
        logger.info("Database upgraded: voices.delivery")
    _drop_projects(engine)


def _drop_projects(engine: Engine) -> None:
    """Projects were removed: rebuild audios and scripts without projects_id, then drop projects.

    SQLite cannot drop a column that a table-level FOREIGN KEY uses (which is how SQLAlchemy wrote
    them), so both tables are rebuilt the way sqlite.org documents ("making other kinds of table schema
    changes"): with foreign keys off, create the new table, copy every row, drop the old one, rename.
    Foreign keys stay off until the end, so nothing cascades (scripts.projects_id was ON DELETE CASCADE,
    script_sections cascade from scripts); a foreign key check runs before the commit. A backup of the
    database is written first.
    """
    names = inspect(engine).get_table_names()
    if "projects" not in names:
        return
    rebuild = [name for name in ("audios", "scripts")
               if name in names and "projects_id" in {c["name"] for c in inspect(engine).get_columns(name)}]
    raw = engine.raw_connection()
    try:
        db = cast(sqlite3.Connection, raw.driver_connection)
        backup = database_path().with_name(f"{database_path().stem}-before-projects-removal.db")
        if not backup.exists():
            with sqlite3.connect(backup) as target:
                db.backup(target)
            target.close()
        previous = db.isolation_level
        db.isolation_level = None  # explicit BEGIN/COMMIT; PRAGMA foreign_keys only changes outside a transaction
        cursor = db.cursor()
        cursor.execute("PRAGMA foreign_keys = OFF")
        try:
            cursor.execute("BEGIN")
            for name in rebuild:
                _rebuild_table(cursor, engine, name)
            cursor.execute("DROP TABLE projects")
            problems = cursor.execute("PRAGMA foreign_key_check").fetchall()
            if problems:
                raise RuntimeError(f"Foreign key check failed after removing projects: {problems[:5]}")
            cursor.execute("COMMIT")
        except Exception:
            cursor.execute("ROLLBACK")
            raise
        finally:
            cursor.execute("PRAGMA foreign_keys = ON")
            db.isolation_level = previous
    finally:
        raw.close()
    logger.info(f"Database upgraded: projects removed (backup: {backup.name})")


def _rebuild_table(cursor, engine: Engine, name: str) -> None:
    """Recreate `name` from its current model (which has no projects_id) and copy the rows across."""
    model = Base.metadata.tables[name]
    copies = MetaData()
    for table in Base.metadata.sorted_tables:  # so the new table's foreign keys can name their targets
        table.to_metadata(copies)
    fresh = model.to_metadata(copies, name=f"{name}__rebuild")
    existing = {row[1] for row in cursor.execute(f'PRAGMA table_info("{name}")')}
    columns = ", ".join(f'"{column.name}"' for column in model.columns if column.name in existing)
    cursor.execute(str(CreateTable(fresh).compile(dialect=engine.dialect)))
    cursor.execute(f'INSERT INTO "{fresh.name}" ({columns}) SELECT {columns} FROM "{name}"')
    cursor.execute(f'DROP TABLE "{name}"')
    cursor.execute(f'ALTER TABLE "{fresh.name}" RENAME TO "{name}"')
    for index in model.indexes:
        cursor.execute(str(CreateIndex(index).compile(dialect=engine.dialect)))


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
