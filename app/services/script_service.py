"""ScriptService: scripts, lessons and multi-speaker dialogue → narrated audio.

A script body is parsed into sections (one per paragraph or speaker line)
grouped under chapters and headings. Each section is generated into takes;
the selected takes are joined with pauses into the final render.
"""

import re
from collections.abc import Callable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.constants.audio import PAUSE_PARAGRAPH_MS, PAUSE_SECTION_MS
from app.constants.audio_source import AudioSource
from app.constants.jobs import JobType
from app.constants.status import Status
from app.exceptions import NotFoundError, ValidationError
from app.models import Audio, Script, ScriptSection, Take
from app.services.audio_service import audio_service
from app.services.job_service import job_service
from app.services.system_service import system_service
from app.services.tts_service import split_sentences, tts_service
from app.utils import audio as au
from app.utils.database import deleted_result, read_session, serialize, transaction
from app.utils.files import remove_file, subdir, unique_path
from app.utils.logger import logger
from app.utils.validation import require_name

DEFAULT_SPEAKER = "*"

_CHAPTER = re.compile(r"^(#\s+|(lesson|chapter|part|unit|module)\b)", re.IGNORECASE)
_SECTION = re.compile(
    r"^(##+\s+|(section|topic|scene|introduction|intro|summary|conclusion|example|exercise|overview|recap|outro)\b)",
    re.IGNORECASE,
)
_SPEAKER = re.compile(r"^([A-Z][\w'\-]*(?:\s[A-Z][\w'\-]*){0,2})\s*:\s+(.+)$")
_PAUSE_ONLY = re.compile(r"^\[pause(?:\s+(\d+)\s*(ms|s)?)?\]$", re.IGNORECASE)

SECTION_FIELDS = ("voices_id", "speed", "pitch", "emotion", "style", "pause_after_ms", "text", "speaker")


def _is_title(line: str) -> bool:
    words = line.split()
    return 0 < len(words) <= 8 and len(line) <= 60 and not re.search(r"[.!?,;:]$", line)


_MINOR_WORDS = {"a", "an", "and", "as", "at", "for", "in", "of", "on", "or", "the", "to", "vs", "with"}


def _is_title_case(line: str) -> bool:
    words = [w for w in re.findall(r"[A-Za-z][\w'\-]*", line)]
    return bool(words) and len(words) <= 6 and all(w[0].isupper() or w.lower() in _MINOR_WORDS for w in words)


def parse_script(body: str, speak_headings: bool = False) -> list[dict]:
    """Parse a script into ordered section dicts (chapter, heading, speaker, text, pause_after_ms)."""
    sections: list[dict] = []
    chapter = heading = ""
    for block in re.split(r"\n\s*\n", body.replace("\r\n", "\n").strip()):
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        if len(lines) == 1 and (pause := _PAUSE_ONLY.match(lines[0])):
            if sections:
                amount = int(pause.group(1) or 1000)
                sections[-1]["pause_after_ms"] += amount * 1000 if (pause.group(2) or "ms").lower() == "s" else amount
            continue
        first = lines[0]
        title_like = _is_title(first.lstrip("# ")) and not _SPEAKER.match(first)
        is_chapter = title_like and bool(_CHAPTER.match(first))
        is_heading = title_like and not is_chapter and (bool(_SECTION.match(first)) or _is_title_case(first))
        if is_chapter or is_heading:
            title = first.lstrip("# ").strip()
            if is_chapter:
                chapter, heading = title, ""
            else:
                heading = title
            if speak_headings:
                sections.append(_section(chapter, heading, "", title))
            lines = lines[1:]
            if not lines:
                continue
        # Each speaker line becomes its own section; following plain lines continue it.
        buffer: list[str] = []
        speaking: dict | None = None
        for line in lines:
            match = _SPEAKER.match(line)
            if match:
                if buffer:
                    sections.append(_section(chapter, heading, "", " ".join(buffer)))
                    buffer = []
                speaking = _section(chapter, heading, match.group(1).strip(), match.group(2).strip())
                sections.append(speaking)
            elif speaking is not None:
                speaking["text"] += " " + line
            else:
                buffer.append(line)
        if buffer:
            sections.append(_section(chapter, heading, "", " ".join(buffer)))

    # Automatic pauses: longer at structure changes.
    for index, section in enumerate(sections):
        nxt = sections[index + 1] if index + 1 < len(sections) else None
        boundary = nxt is None or nxt["chapter"] != section["chapter"] or nxt["heading"] != section["heading"]
        section["pause_after_ms"] += 0 if nxt is None else (PAUSE_SECTION_MS if boundary else PAUSE_PARAGRAPH_MS)
        section["position"] = index
    return sections


def _section(chapter: str, heading: str, speaker: str, text: str) -> dict:
    return {"chapter": chapter, "heading": heading, "speaker": speaker, "text": text, "pause_after_ms": 0}


def detect_speakers(sections: list[dict]) -> list[str]:
    seen: list[str] = []
    for section in sections:
        if section["speaker"] and section["speaker"] not in seen:
            seen.append(section["speaker"])
    return seen


def outline(sections: list[dict]) -> list[dict]:
    """Chapters → headings → section count, for the structure tree."""
    tree: list[dict] = []
    for section in sections:
        if not tree or tree[-1]["chapter"] != section["chapter"]:
            tree.append({"chapter": section["chapter"], "headings": []})
        headings = tree[-1]["headings"]
        if not headings or headings[-1]["heading"] != section["heading"]:
            headings.append({"heading": section["heading"], "sections": 0, "sentences": 0})
        headings[-1]["sections"] += 1
        headings[-1]["sentences"] += len(split_sentences(section["text"]))
    return tree


class ScriptService:
    parse = staticmethod(parse_script)
    detect_speakers = staticmethod(detect_speakers)

    # ------------------------------------------------------------ serialization

    def section_dict(self, section: ScriptSection) -> dict:
        data = serialize(section)
        data["takes"] = [serialize(t) for t in section.takes]
        selected = next((t for t in section.takes if t.selected), None)
        data["selected_audios_id"] = selected.audios_id if selected else None
        return data

    def to_dict(self, script: Script, with_sections: bool = True) -> dict:
        data = serialize(script)
        if with_sections:
            data["sections"] = [self.section_dict(s) for s in script.sections]
            raw = [{"chapter": s.chapter, "heading": s.heading, "speaker": s.speaker, "text": s.text}
                   for s in script.sections]
            data["speakers"] = detect_speakers(raw)
            data["outline"] = outline(raw)
        return data

    def _get(self, session: Session, scripts_id: int) -> Script:
        script = session.get(Script, scripts_id)
        if script is None:
            raise NotFoundError(f"Script {scripts_id} not found", field="scripts_id")
        return script

    def _section(self, session: Session, script_sections_id: int) -> ScriptSection:
        section = session.get(ScriptSection, script_sections_id)
        if section is None:
            raise NotFoundError(f"Section {script_sections_id} not found", field="script_sections_id")
        return section

    # ------------------------------------------------------------ CRUD

    def create(self, title: str, body: str = "", projects_id: int | None = None,
               speaker_map: dict | None = None, settings: dict | None = None) -> dict:
        with transaction() as session:
            script = Script(title=require_name(title, "title", 200), body=body, projects_id=projects_id,
                            speaker_map=speaker_map or {}, settings=settings or {})
            session.add(script)
            session.flush()
            self._sync_sections(session, script)
            logger.info(f"Created script {script.scripts_id} with {len(script.sections)} sections")
            return self.to_dict(script)

    def get(self, scripts_id: int) -> dict:
        with read_session() as session:
            return self.to_dict(self._get(session, scripts_id))

    def list_scripts(self, projects_id: int | None = None) -> list[dict]:
        with read_session() as session:
            query = select(Script)
            if projects_id is not None:
                query = query.where(Script.projects_id == projects_id)
            return [self.to_dict(s, with_sections=False) for s in session.scalars(query.order_by(Script.updated_at.desc()))]

    def update(self, scripts_id: int, title: str | None = None, body: str | None = None,
               speaker_map: dict | None = None, settings: dict | None = None) -> dict:
        with transaction() as session:
            script = self._get(session, scripts_id)
            if title is not None:
                script.title = require_name(title, "title", 200)
            if speaker_map is not None:
                script.speaker_map = {k: v for k, v in speaker_map.items() if v}
            if settings is not None:
                script.settings = {**(script.settings or {}), **settings}
            if body is not None and body != script.body or settings and "speak_headings" in settings:
                script.body = body if body is not None else script.body
                self._sync_sections(session, script)
            return self.to_dict(script)

    def save(self, scripts_id: int | None = None, status: int | None = None, **fields) -> dict:
        """One entry point: create (no id), delete (status = Deleted) or update."""
        if scripts_id is None:
            return self.create(**fields)
        if status == Status.DELETED.code:
            self.delete(scripts_id)
            return deleted_result("scripts_id", scripts_id)
        fields.pop("projects_id", None)  # a script stays in its project
        return self.update(scripts_id, **fields)

    def _sync_sections(self, session: Session, script: Script) -> None:
        """Re-parse the body, keeping existing sections (and their takes) whose text is unchanged."""
        parsed = parse_script(script.body or "", bool((script.settings or {}).get("speak_headings")))
        existing: dict[tuple[str, str], list[ScriptSection]] = {}
        for section in script.sections:
            existing.setdefault((section.speaker, section.text), []).append(section)
        keep: list[ScriptSection] = []
        for item in parsed:
            candidates = existing.get((item["speaker"], item["text"]))
            section = candidates.pop(0) if candidates else ScriptSection(text=item["text"], speaker=item["speaker"])
            section.position, section.chapter, section.heading = item["position"], item["chapter"], item["heading"]
            section.pause_after_ms = item["pause_after_ms"]
            keep.append(section)
        script.sections[:] = keep  # delete-orphan removes the rest (and their takes)
        session.flush()

    def delete(self, scripts_id: int) -> None:
        with transaction() as session:
            script = self._get(session, scripts_id)
            audio_ids = [t.audios_id for s in script.sections for t in s.takes]
            session.delete(script)
        for audios_id in audio_ids:
            try:
                audio_service.delete(audios_id)
            except NotFoundError:
                pass

    # ------------------------------------------------------------ speakers / sections

    def map_speakers(self, scripts_id: int, mapping: dict[str, int | None]) -> dict:
        """Assign voices to speakers ("*" = narrator/default). Manual overrides replace auto mapping."""
        with transaction() as session:
            script = self._get(session, scripts_id)
            merged = {**(script.speaker_map or {}), **mapping}
            script.speaker_map = {k: v for k, v in merged.items() if v}
            return self.to_dict(script)

    def auto_map_speakers(self, scripts_id: int, voices_ids: list[int]) -> dict:
        """Round-robin available voices onto unmapped speakers."""
        script = self.get(scripts_id)
        mapping = dict(script["speaker_map"])
        free = [v for v in voices_ids if v not in mapping.values()] or voices_ids
        for index, speaker in enumerate(s for s in script["speakers"] if s not in mapping):
            if free:
                mapping[speaker] = free[index % len(free)]
        return self.map_speakers(scripts_id, mapping)

    def update_section(self, script_sections_id: int, **fields) -> dict:
        unknown = set(fields) - set(SECTION_FIELDS)
        if unknown:
            raise ValidationError(f"Cannot update section fields: {', '.join(sorted(unknown))}")
        with transaction() as session:
            section = self._section(session, script_sections_id)
            for key, value in fields.items():
                setattr(section, key, value)
            if "text" in fields:
                section.script.body = self._body_from_sections(section.script)
            return self.section_dict(section)

    def _body_from_sections(self, script: Script) -> str:
        """Rebuild the body after a section edit so body and sections stay in sync."""
        lines, chapter, heading = [], None, None
        for section in script.sections:
            if section.chapter != chapter and section.chapter:
                lines.append(section.chapter)
            if section.heading != heading and section.heading:
                lines.append(section.heading)
            chapter, heading = section.chapter, section.heading
            lines.append(f"{section.speaker}: {section.text}" if section.speaker else section.text)
        return "\n\n".join(lines)

    def reorder(self, scripts_id: int, ordered_ids: list[int]) -> dict:
        with transaction() as session:
            script = self._get(session, scripts_id)
            by_id = {s.script_sections_id: s for s in script.sections}
            if set(ordered_ids) != set(by_id):
                raise ValidationError("Reorder must include every section exactly once", field="ordered_ids")
            for position, section_id in enumerate(ordered_ids):
                by_id[section_id].position = position
            script.sections.sort(key=lambda s: s.position)
            script.body = self._body_from_sections(script)
            return self.to_dict(script)

    def resolve_voice(self, section: dict, script: dict) -> int | None:
        mapping = script.get("speaker_map") or {}
        return (section.get("voices_id") or mapping.get(section.get("speaker") or "")
                or mapping.get(DEFAULT_SPEAKER) or system_service.get_setting("default_voices_id"))

    # ------------------------------------------------------------ generation

    def generate_section(self, script_sections_id: int, seed: int | None = None,
                         progress: Callable[[float], None] | None = None) -> dict:
        """Generate a new take for one section and select it."""
        with read_session() as session:
            section = self._section(session, script_sections_id)
            section_data = self.section_dict(section)
            script = self.to_dict(section.script, with_sections=False)
        defaults = script.get("settings") or {}
        params = {
            key: section_data.get(key) if section_data.get(key) is not None else defaults.get(key)
            for key in ("speed", "pitch", "emotion", "style")
        }
        audio = tts_service.generate(
            section_data["text"],
            self.resolve_voice(section_data, script),
            defaults.get("model_key"),
            projects_id=script.get("projects_id"),
            name=f"{script['title']} · {section_data['heading'] or 'section'} {section_data['position'] + 1}",
            seed=seed,
            progress=progress,
            **{k: v for k, v in params.items() if v is not None},
        )
        with transaction() as session:
            section = self._section(session, script_sections_id)
            for take in section.takes:
                take.selected = False
            number = max((t.take_number for t in section.takes), default=0) + 1
            section.takes.append(Take(audios_id=audio["audios_id"], take_number=number, selected=True))
            session.flush()
            return self.section_dict(section)

    def generate_all(self, scripts_id: int, regenerate: bool = False,
                     progress: Callable[[float], None] | None = None) -> dict:
        script = self.get(scripts_id)
        todo = [s for s in script["sections"] if regenerate or not s["selected_audios_id"]]
        for index, section in enumerate(todo):
            self.generate_section(section["script_sections_id"])
            if progress:
                progress((index + 1) / max(len(todo), 1))
        return self.get(scripts_id)

    def select_take(self, takes_id: int) -> dict:
        with transaction() as session:
            take = session.get(Take, takes_id)
            if take is None:
                raise NotFoundError(f"Take {takes_id} not found", field="takes_id")
            for other in take.section.takes:
                other.selected = other.takes_id == takes_id
            return self.section_dict(take.section)

    def delete_take(self, takes_id: int) -> dict:
        with transaction() as session:
            take = session.get(Take, takes_id)
            if take is None:
                raise NotFoundError(f"Take {takes_id} not found", field="takes_id")
            section = take.section
            audios_id, was_selected = take.audios_id, take.selected
            section.takes.remove(take)
            if was_selected and section.takes:
                section.takes[-1].selected = True
            session.flush()
            result = self.section_dict(section)
        audio_service.delete(audios_id)
        return result

    def render(self, scripts_id: int, progress: Callable[[float], None] | None = None) -> dict:
        """Join the selected takes (plus optional intro/outro) into the final audio."""
        script = self.get(scripts_id)
        settings = script.get("settings") or {}
        missing = [s["position"] + 1 for s in script["sections"] if not s["selected_audios_id"]]
        if not script["sections"]:
            raise ValidationError("The script has no sections to render")
        if missing:
            raise ValidationError(f"Generate these sections first: {', '.join(map(str, missing[:10]))}")

        clips: list[tuple[int, int]] = [(s["selected_audios_id"], s["pause_after_ms"] or 0) for s in script["sections"]]
        narrator = self.resolve_voice({"speaker": DEFAULT_SPEAKER}, script)
        for key, where in (("intro_text", 0), ("outro_text", None)):
            if (settings.get(key) or "").strip():
                extra = tts_service.generate(settings[key], narrator, settings.get("model_key"),
                                             projects_id=script["projects_id"], name=key.split("_")[0].title())
                clip = (extra["audios_id"], PAUSE_SECTION_MS)
                clips.insert(0, clip) if where == 0 else clips.append(clip)

        sources = [audio_service.get(audios_id) for audios_id, _ in clips]
        sr = max(s["sample_rate"] for s in sources)
        parts = []
        for index, (source, (_, pause)) in enumerate(zip(sources, clips)):
            y, _ = au.load(source["path"], sr=sr)
            parts.append(y)
            if index < len(clips) - 1:
                parts.append(au.silence(pause / 1000, sr))
            if progress:
                progress((index + 1) / len(clips) * 0.8)
        y = au.concat(parts)
        steps = audio_service.resolve_steps(preset=settings.get("preset") or "Raw")
        y = audio_service.process_array(y, sr, steps) if steps else y
        path = au.save(unique_path(subdir("audio", "renders"), script["title"], "wav"), y, sr, ai_generated=True)

        with transaction() as session:
            audio = audio_service.register(
                session, path, AudioSource.RENDERED, name=f"{script['title']} (final)", ai_generated=True,
                params={"scripts_id": scripts_id, "takes": [c[0] for c in clips], "preset": settings.get("preset")},
                projects_id=script["projects_id"], y=y, sr=sr,
            )
            old_final = self._get(session, scripts_id).final_audios_id
            self._get(session, scripts_id).final_audios_id = audio.audios_id
            result = audio_service.to_dict(audio)
        if old_final:
            with transaction() as session:
                old = session.get(Audio, old_final)
                if old is not None:
                    path_to_remove = old.path
                    session.delete(old)
                else:
                    path_to_remove = None
            remove_file(path_to_remove)
        if progress:
            progress(1.0)
        logger.info(f"Rendered script {scripts_id}: {result['duration']:.1f}s")
        return result

    def generate(self, scripts_id: int, regenerate: bool = False,
                 progress: Callable[[float], None] | None = None) -> dict:
        """Generate every missing section and render the final audio."""
        sub = (lambda lo, hi: (lambda v: progress(lo + (hi - lo) * v))) if progress else (lambda lo, hi: None)
        self.generate_all(scripts_id, regenerate, progress=sub(0.0, 0.85))
        return {"script": self.get(scripts_id), "audio": self.render(scripts_id, progress=sub(0.85, 1.0))}

    def timeline(self, scripts_id: int, estimate_seconds_per_char: float = 0.065) -> list[dict]:
        """Clips laid out in render order; missing sections get an estimated length."""
        script = self.get(scripts_id)
        clips, t = [], 0.0
        speakers = detect_speakers(script["sections"])
        for section in script["sections"]:
            audios_id = section["selected_audios_id"]
            duration = audio_service.get(audios_id)["duration"] if audios_id else \
                max(0.5, len(section["text"]) * estimate_seconds_per_char)
            label = f"{section['speaker'] + ': ' if section['speaker'] else ''}{section['text'][:40]}"
            clips.append({
                "start": t, "end": t + duration, "label": label, "key": section["script_sections_id"],
                "audios_id": audios_id, "missing": audios_id is None,
                "group": speakers.index(section["speaker"]) + 1 if section["speaker"] in speakers else 0,
            })
            t += duration + (section["pause_after_ms"] or 0) / 1000
        return clips

    # ------------------------------------------------------------ background wrappers

    def generate_async(self, scripts_id: int, regenerate: bool = False) -> dict:
        script = self.get(scripts_id)
        return job_service.submit(JobType.SCRIPT_RENDER,
                                  lambda ctx: self.generate(scripts_id, regenerate, progress=ctx.progress),
                                  title=f"Render script: {script['title']}", params={"scripts_id": scripts_id})

    def generate_section_async(self, script_sections_id: int, seed: int | None = None) -> dict:
        return job_service.submit(
            JobType.SECTION_GENERATE,
            lambda ctx: {"section": self.generate_section(script_sections_id, seed, progress=ctx.progress)},
            title=f"Generate section {script_sections_id}", params={"script_sections_id": script_sections_id},
        )

    def generate_all_async(self, scripts_id: int, regenerate: bool = False) -> dict:
        return job_service.submit(
            JobType.SCRIPT_RENDER,
            lambda ctx: {"script": self.generate_all(scripts_id, regenerate, progress=ctx.progress)},
            title=f"Generate script {scripts_id}", params={"scripts_id": scripts_id},
        )

    def render_async(self, scripts_id: int) -> dict:
        return job_service.submit(JobType.PROJECT_RENDER,
                                  lambda ctx: {"audio": self.render(scripts_id, progress=ctx.progress)},
                                  title=f"Render script {scripts_id}", params={"scripts_id": scripts_id})


script_service = ScriptService()
