# Script to audio

`ScriptService` (`app/services/script_service.py`) turns scripts, lessons and dialogues into narrated audio.

## Script format

```
Lesson 1                       ← chapter  (Lesson/Chapter/Part/Unit/Module …, or "# Title")

Introduction                   ← heading  (Section/Topic/Scene/Introduction/Summary/Example …,
                                            "## Title", or a short Title Case line)
Welcome to today's lesson.     ← paragraph → one section

Teacher: What is a wave?       ← speaker line → one section (speaker "Teacher")
Student: I'm not sure.
It sounds hard.                ← continues the Student line

[pause 2s]                     ← a line on its own adds pause after the previous section
```

`parse_script(body, speak_headings=False)` returns ordered sections with `chapter`, `heading`, `speaker`, `text`, `pause_after_ms` and `position`. It sets pauses automatically:
- 600 ms between paragraphs
- 1200 ms at a chapter or heading boundary
- plus any manual `[pause …]` lines

Inline `[pause 800ms]` tags inside text are handled by TTS. With `speak_headings`, headings become spoken sections.

## Voices and settings

Each section's voice is resolved in this order:

1. the section's own `voices_id`
2. `speaker_map[speaker]`
3. `speaker_map["*"]` (narrator)
4. the `default_voices_id` setting
5. the engine's default voice

- `map_speakers()` sets manual mappings.
- `auto_map_speakers()` assigns voices round-robin to speakers that have none yet.
- `update_section()` sets per-section voice, speed, pitch, emotion, style and pause.
- Script-level defaults live in `scripts.settings`: `model_key`, `speed`, `emotion`, `style`, the final `preset`, `speak_headings`, `intro_text` and `outro_text`.

## Takes

- `generate_section(id)` creates a new take (an `audios` row plus a `takes` row) and selects it.
- `select_take()`, `delete_take()`: only the selected take enters the render.
- Editing the body re-parses it. Sections whose (speaker, text) did not change keep their takes.
- `reorder()` changes the order and rewrites the body to match.

## Rendering

- `render(scripts_id)` joins the selected takes with each section's pause, adds the optional intro and outro, applies the final clean-up preset (for example Lesson, which targets −16 LUFS), and stores the result as `scripts.final_audios_id`. The previous final render is replaced.
- `generate(scripts_id)` generates the missing sections and then renders.
- `timeline(scripts_id)` lays out clips for the Studio timeline, estimating the length of sections not yet generated.

Every step has an `*_async` wrapper that runs as a background job.

## UI

- **Script to Audio page:** a script list, the editor (autosaves after 0.8 s), and Structure / Speakers / Section / Script settings tabs. Actions: generate a take, generate all, render, and play.
- **Studio page:** the project and script picker, a sections table, a voice panel, and a timeline with clips over the final waveform and transport.
