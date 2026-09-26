---
name: voxlabs
description: Index of VoxLabs task skills. Start here, then open the skill that matches the task.
---

# VoxLabs skills

These are short, task-oriented workflows for working on VoxLabs. They are documentation, not runtime code; the application itself lives in `app/`.

| Skill | Use it when |
|---|---|
| [voice-cloning](voice-cloning/SKILL.md) | Changing sample validation, consent, voice profiles, revoke/delete |
| [tts](tts/SKILL.md) | Changing speech generation, parameters, sentence regeneration |
| [script-to-audio](script-to-audio/SKILL.md) | Changing script parsing, speakers, takes, lesson rendering |
| [audio-editing](audio-editing/SKILL.md) | Changing the waveform editor or edit operations |
| [audio-enhancement](audio-enhancement/SKILL.md) | Changing DSP steps, presets, loudness |
| [model-management](model-management/SKILL.md) | Adding engines, install/load logic, device selection |
| [development](development/SKILL.md) | Setup, conventions, testing, adding a feature end to end |

## Rules that apply to every skill

- Logic goes in `app/services/`. UI pages and API routes only call services.
- Every table declares `<table>_id`, `status` (`Integer`, `default=Status.X.code`), `created_at` and `updated_at`. Use `.code` for status everywhere.
- Multi-row changes go in one `with transaction() as session:`.
- Slow work goes through `job_service.submit()`, so it never blocks the Qt thread.
- Consent before cloning, AI-generated labelling, local-first defaults and complete revoke/delete are non-negotiable.
- Run `uv run pytest` before finishing.
