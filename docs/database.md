# Database

SQLite through SQLAlchemy 2.0. All infrastructure is in `app/utils/database.py`:

- `get_engine()`: the engine for `data/database/voxlabs.db` (override with `VOXLABS_DB_PATH` or `VOXLABS_DATA_DIR`). It uses WAL mode and turns foreign keys on.
- `Base`: a plain `DeclarativeBase`.
- `transaction()`: a unit of work that commits on success and rolls back on any exception.
- `read_session()`: a read-only session.
- `init_db()`: `create_all` for every model.
- `serialize(row)`: converts a row to a dict. Datetimes become ISO-8601 UTC strings, and `status` gets a readable `status_label` next to its integer code.

## Naming rules

Every table:

- is a clear plural name (`voices`, `voice_samples`, `script_sections`, …);
- has a `<table_name>_id` INTEGER primary key (never a bare `id`);
- has `status` INTEGER (always the shared `Status` const), plus `created_at` and `updated_at` (timezone-aware UTC; `updated_at` uses `onupdate`).

Each model declares these four columns explicitly in its own file.

## Status constants

`app/constants/base_enum.py` defines `BaseEnum`, whose members are `(code, value)`:

```python
class Status(BaseEnum):
    ACTIVE = (1, "Active")
    INACTIVE = (2, "Inactive")
    PENDING = (3, "Pending")
    IN_PROGRESS = (4, "InProgress")
    COMPLETED = (5, "Completed")
    FAILED = (6, "Failed")
    CANCELLED = (7, "Cancelled")
    DELETED = (8, "Deleted")

Status.IN_PROGRESS.code   # 4  (stored in the column)
Status.IN_PROGRESS.value  # "InProgress"
Status(4)                 # Status.IN_PROGRESS
```

Columns are plain INTEGER and code always uses `.code`:

```python
status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)

voice.status = Status.INACTIVE.code
select(Audio).where(Audio.status != Status.DELETED.code)
```

The `status` column uses `Status` only. When a table needs its own numbered state, it gets a separate `<name>_status` column with its own BaseEnum. The current example is `voices.consent_status` → `ConsentStatus` (NotRequired, Granted, Revoked).

## Tables

| Table | Purpose | Key columns |
|---|---|---|
| `users` | Local profiles | name, email |
| `voices` | Cloned or preset voices | users_id, name, language, model_key, source (`clone`/`preset`), engine_voice, consent_status, profile (JSON), storage_dir, sample_count |
| `voice_samples` | Reference recordings | voices_id, path, duration, sample_rate, quality (JSON), sha256 |
| `voice_consents` | Consent audit trail | voices_id, granted_by, speaker_name, statement, granted_at, revoked_at |
| `audios` | Every audio file | projects_id, parent_audios_id, path, original_path, source, ai_generated, duration, sample_rate, channels, format, codec, file_size, loudness, params (JSON) |
| `projects` | Production projects | users_id, name, project_type, settings, edit_state (JSON) |
| `scripts` | Scripts and lessons | projects_id, title, body, speaker_map, settings, final_audios_id |
| `script_sections` | Generatable units | scripts_id, position, chapter, heading, speaker, text, voice/speed/pitch/emotion/style overrides, pause_after_ms |
| `takes` | Renditions of a section | script_sections_id, audios_id, take_number, selected |
| `jobs` | Background work | users_id, job_type, title, progress, error, params, result, started_at, finished_at |
| `models` | Model catalog | key, name, model_type, backend, version, size_mb, vram_mb, capabilities, online, installed_path |

What `status` means per table:
- **jobs:** Pending → InProgress → Completed / Failed / Cancelled.
- **models:** Active when installed, Inactive otherwise.
- **voices:** Active, or Inactive after revocation.
- **voice_consents:** Active, or Inactive once revoked (`revoked_at` is set).

Large binary data never goes in the database. Rows store paths under `data/`.

## Transactions

Services open transactions. Anything that must succeed or fail together happens in one block. For example, `CloneService.clone` creates the voice, consent record and samples, and builds the profile, inside a single `transaction()`. If any step raises, the rows are rolled back and the voice's folder is removed.

Helpers that accept a `session` argument (`audio_service.register`, `voice_service.create_in`, `consent_service.record`) join the caller's transaction instead of committing on their own.

## Schema changes

`init_db()` creates missing tables. The schema is new in 3.0, so there are no migrations yet. When a column changes on a released version, add a small migration step to `init_db()`.
