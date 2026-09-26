---
name: script-to-audio
description: Workflow and rules for VoxLabs scripts, lessons, multi-speaker dialogue, takes and final rendering.
---

# Script / lesson to audio

## Purpose

Convert a structured script, lesson or dialogue into sections, generate takes per section, and render a final narrated audio.

## Workflow

1. `parse_script(body, speak_headings)` returns sections with chapter, heading, speaker, text and automatic pauses (600 ms between paragraphs, 1200 ms at boundaries, plus `[pause]` lines).
2. `script_service.create()` or `update()` stores the body. `_sync_sections()` keeps sections (and their takes) whose (speaker, text) is unchanged.
3. Map voices with `map_speakers()` or `auto_map_speakers()`. Set per-section overrides with `update_section()`. Resolution order: section voice → speaker map → `"*"` narrator → `default_voices_id` setting.
4. `generate_section()` adds a take and selects it. `generate_all()` fills missing takes. `select_take()` and `delete_take()` manage them.
5. `render()` joins the selected takes with pauses, adds the intro/outro, applies the final preset, and sets `final_audios_id`. `generate()` does steps 4 and 5 together.
6. `timeline()` lays out clips for the Studio.

## Important rules

- Only selected takes are rendered. Rendering fails with a clear message listing the sections still missing.
- Parsing must never silently drop spoken text. Only lines recognised as headings are treated as headings.
- Keep body and sections consistent. Section text edits and reorders rewrite the body (`_body_from_sections`).
- Long operations need `*_async` wrappers for the UI.

## References

- `app/services/script_service.py`
- `app/models/script.py`, `script_section.py`, `take.py`
- `app/ui/pages/script_page.py`, `studio_page.py`
- `docs/script-to-audio.md`

## Testing

`tests/test_script_service.py` covers lesson structure, speaker lines and continuations, voice mapping and overrides, takes and selection, rendering with an intro, body edits keeping takes, and reorder.
