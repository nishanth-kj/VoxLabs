---
name: audio-editing
description: Workflow and rules for the VoxLabs non-destructive waveform editor and edit operations.
---

# Audio editing

## Purpose

Edit audio without ever touching the source file. Edits are an operation list that is replayed, previewed, rendered to a new file, and autosaved into the project.

## Workflow

1. The editor loads an audio: `audio_service.get()` plus `au.load()`, then restores saved ops with `project_service.load_edit_ops()`.
2. Each user action becomes an op dict (see the table in `docs/audio-engine.md`), applied with `audio_service.apply_edit_ops(current, sr, [op])`. The page keeps `ops` and a state per op for undo and redo.
3. Clipboard selections are saved with `audio_service.save_clip()`, and `paste`/`insert` ops reference that file.
4. **Render** runs `audio_service.render_edits(audios_id, ops)` as a background job and creates a new `audios` row with `parent_audios_id`.
5. **Split and export** use `audio_service.materialize(audios_id, ops)` first.
6. Autosave: `project_service.save_edit_ops(projects_id, audios_id, ops)` every 30 s (when enabled) and on close.

## Important rules

- Never write to `audio["path"]` or `audio["original_path"]` of an existing audio.
- New operations go into `AudioService.apply_edit_ops` (the service), not the page, so the API (`POST /api/audio/process` with `ops`) gets them too.
- Keyboard shortcuts: Space, Ctrl+Z, Ctrl+Shift+Z / Ctrl+Y, Ctrl+X/C/V, Delete, Ctrl+A, Ctrl+D, Ctrl+T, Home/End.
- Heavy ops (`enhance`) run through `BasePage.run()`. Never block the UI thread.

## References

- `app/services/audio_service.py` (`apply_edit_ops`, `render_edits`, `split`, `join`, `materialize`)
- `app/ui/pages/editor_page.py`
- `app/ui/widgets/waveform.py`, `timeline.py`, `audio_player.py`

## Testing

`tests/test_audio_service.py::test_edit_ops` and `test_render_edits_split_join_and_export`. Add a case there for every new op.
