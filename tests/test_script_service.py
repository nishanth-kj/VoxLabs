import pytest

from app.constants.audio import PAUSE_PARAGRAPH_MS, PAUSE_SECTION_MS
from app.exceptions import ValidationError
from app.services.script_service import detect_speakers, outline, parse_script, script_service
from app.services.voice_service import voice_service

LESSON = """Lesson 1

Introduction

Welcome to today's lesson. We will learn about sound.

Section 1

First, we will learn what a wave is.

[pause 2s]

Section 2

Now let's understand frequency.
"""

DIALOGUE = """Teacher: Welcome to today's lesson.

Student: What does this concept mean?

Teacher: It means sound is a wave.
It travels through air."""


def test_parse_lesson_structure():
    sections = parse_script(LESSON)
    assert [s["heading"] for s in sections] == ["Introduction", "Section 1", "Section 2"]
    assert all(s["chapter"] == "Lesson 1" for s in sections)
    assert sections[0]["pause_after_ms"] == PAUSE_SECTION_MS
    assert sections[1]["pause_after_ms"] == PAUSE_SECTION_MS + 2000
    tree = outline(sections)
    assert tree[0]["chapter"] == "Lesson 1" and len(tree[0]["headings"]) == 3


def test_parse_speakers_and_continuations():
    sections = parse_script(DIALOGUE)
    assert [s["speaker"] for s in sections] == ["Teacher", "Student", "Teacher"]
    assert sections[2]["text"].endswith("It travels through air.")
    assert detect_speakers(sections) == ["Teacher", "Student"]
    assert sections[0]["pause_after_ms"] == PAUSE_PARAGRAPH_MS


def test_speak_headings_option():
    sections = parse_script(LESSON, speak_headings=True)
    assert sections[0]["text"] == "Lesson 1"


def test_voice_mapping_and_overrides():
    a = voice_service.create("Voice A")
    b = voice_service.create("Voice B")
    script = script_service.create("Dialogue", DIALOGUE)
    script = script_service.auto_map_speakers(script["scripts_id"], [a["voices_id"], b["voices_id"]])
    assert script["speaker_map"] == {"Teacher": a["voices_id"], "Student": b["voices_id"]}
    script = script_service.map_speakers(script["scripts_id"], {"Student": a["voices_id"]})
    student = script["sections"][1]
    assert script_service.resolve_voice(student, script) == a["voices_id"]
    section = script_service.update_section(student["script_sections_id"], voices_id=b["voices_id"])
    assert script_service.resolve_voice(section, script) == b["voices_id"]


def test_generate_takes_and_render():
    script = script_service.create("Lesson", LESSON, settings={"intro_text": "Welcome to the course."})
    first = script["sections"][0]
    section = script_service.generate_section(first["script_sections_id"])
    section = script_service.generate_section(first["script_sections_id"])
    assert [t["take_number"] for t in section["takes"]] == [1, 2]
    assert [t["selected"] for t in section["takes"]] == [False, True]
    section = script_service.select_take(section["takes"][0]["takes_id"])
    assert section["selected_audios_id"] == section["takes"][0]["audios_id"]

    with pytest.raises(ValidationError, match="Generate these sections"):
        script_service.render(script["scripts_id"])
    result = script_service.generate(script["scripts_id"])
    audio = result["audio"]
    assert audio["ai_generated"] and audio["source"] == "rendered"
    # intro + 3 sections joined by section/manual pauses
    assert audio["duration"] > 3 * PAUSE_SECTION_MS / 1000 + 2.0
    assert script_service.get(script["scripts_id"])["final_audios_id"] == audio["audios_id"]
    assert len(script_service.timeline(script["scripts_id"])) == 3


def test_body_edit_keeps_unchanged_takes_and_reorder():
    script = script_service.create("Edit", DIALOGUE)
    first = script["sections"][0]
    script_service.generate_section(first["script_sections_id"])
    script = script_service.update(script["scripts_id"], body=DIALOGUE + "\n\nStudent: Thanks!")
    assert len(script["sections"]) == 4
    assert script["sections"][0]["takes"], "unchanged section should keep its take"
    ids = [s["script_sections_id"] for s in script["sections"]]
    reordered = script_service.reorder(script["scripts_id"], list(reversed(ids)))
    assert [s["script_sections_id"] for s in reordered["sections"]] == list(reversed(ids))
    assert reordered["body"].startswith("Student: Thanks!")
