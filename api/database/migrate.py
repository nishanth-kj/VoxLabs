"""
Applies pending .sql files in database/migrations, in filename order, tracking
what has already run in a schema_migrations table.

Usage: python -m database.migrate
"""

from pathlib import Path
from database.connection import get_connection
from utils.logger import logger

MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _ensure_migrations_table(conn):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )


def run_migrations():
    with get_connection() as conn:
        _ensure_migrations_table(conn)
        applied = {row["filename"] for row in conn.execute("SELECT filename FROM schema_migrations")}

        pending = sorted(
            f for f in MIGRATIONS_DIR.glob("*.sql") if f.name not in applied
        )

        if not pending:
            logger.info("No pending migrations.")
            return

        for migration_file in pending:
            logger.info(f"Applying migration: {migration_file.name}")
            sql = migration_file.read_text(encoding="utf-8")
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations (filename) VALUES (?)",
                (migration_file.name,),
            )

        logger.info(f"Applied {len(pending)} migration(s).")


if __name__ == "__main__":
    run_migrations()
