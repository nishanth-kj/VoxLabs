import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from database.connection import get_connection


# --- Table structure (see database/migrations/0001_create_voices_table.sql) ---

class VoiceTable(BaseModel):
    """Row shape of the voices table"""
    voice_id: str
    name: str
    consent: bool
    project_id: str
    metadata: Dict[str, Any]
    revoked: bool
    created_at: str


# --- SQL access functions for the voices table ---

def _row_to_voice(row) -> VoiceTable:
    data = dict(row)
    data["consent"] = bool(data["consent"])
    data["revoked"] = bool(data["revoked"])
    data["metadata"] = json.loads(data["metadata"])
    return VoiceTable(**data)


def create_voice(
    voice_id: str,
    name: str,
    consent: bool,
    project_id: str,
    created_at: str,
    metadata: Optional[Dict] = None,
) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO voices (voice_id, name, consent, project_id, metadata, revoked, created_at)
            VALUES (?, ?, ?, ?, ?, 0, ?)
            """,
            (voice_id, name, int(consent), project_id, json.dumps(metadata or {}), created_at),
        )


def get_voice_by_id(voice_id: str) -> Optional[VoiceTable]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM voices WHERE voice_id = ? AND revoked = 0", (voice_id,)
        ).fetchone()
        return _row_to_voice(row) if row else None


def list_voices(project_id: Optional[str] = None) -> List[VoiceTable]:
    with get_connection() as conn:
        if project_id:
            rows = conn.execute(
                "SELECT * FROM voices WHERE revoked = 0 AND project_id = ?", (project_id,)
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM voices WHERE revoked = 0").fetchall()
        return [_row_to_voice(row) for row in rows]


def revoke_voice(voice_id: str) -> None:
    with get_connection() as conn:
        conn.execute("UPDATE voices SET revoked = 1 WHERE voice_id = ?", (voice_id,))
