"""One-off import of voices registered with VoxLabs 2.x (voice_projects/).

VoxLabs 2.x stored consented voices in voice_projects/voices_metadata.json with
their source audio in voice_projects/voices_source/<voice_id>.wav. This script
re-clones each non-revoked voice that had consent=true, carrying the original
consent date into the new consent record.

    uv run python -m scripts.import_legacy_voices [path/to/voice_projects]
"""

import json
import sys
from pathlib import Path

from app.exceptions import AppError
from app.services.clone_service import clone_service
from app.services.system_service import system_service


def main(folder: str = "voice_projects") -> int:
    root = Path(folder)
    metadata_file = root / "voices_metadata.json"
    if not metadata_file.exists():
        print(f"No legacy metadata at {metadata_file}; nothing to import.")
        return 0
    system_service.initialize()
    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    imported = skipped = 0
    for voice_id, data in metadata.items():
        source = root / "voices_source" / f"{voice_id}.wav"
        if data.get("revoked") or not data.get("consent") or not source.exists():
            skipped += 1
            continue
        name = data.get("name") or voice_id
        consent = {
            "confirmed": True,
            "granted_by": "Imported from VoxLabs 2.x consent log",
            "speaker_name": name,
            "statement": f"Consent was recorded by VoxLabs 2.x on {data.get('created_at', 'an unknown date')}.",
        }
        try:
            voice = clone_service.clone([source], name, consent, description="Imported from VoxLabs 2.x")
            print(f"Imported {name} -> voice {voice['voices_id']}")
            imported += 1
        except AppError as exc:
            print(f"Skipped {name}: {exc.message}")
            skipped += 1
    print(f"Done: {imported} imported, {skipped} skipped.")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
