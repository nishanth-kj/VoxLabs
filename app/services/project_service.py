"""ProjectService: projects group scripts, audio, takes and editor state."""

import json
import zipfile
from pathlib import Path

from sqlalchemy import select

from app.constants.audio import AI_GENERATED_TAG
from app.constants.project_type import ProjectType
from app.constants.status import Status
from app.exceptions import NotFoundError, ProjectError, service_error
from app.models import Audio, Project, Script, ScriptSection, Take
from app.models.request import ProjectRequest
from app.services.audio_service import audio_service
from app.services.script_service import script_service
from app.utils.database import deleted_result, read_session, serialize, transaction
from app.utils.files import copy_file, extension, remove_file, safe_name, subdir, unique_path
from app.utils.logger import logger
from app.utils.time import utcnow
from app.utils.validation import Validation


class ProjectService:
    def to_dict(self, project: Project) -> dict:
        data = serialize(project)
        return data

    def _get(self, session, projects_id: int) -> Project:
        project = session.get(Project, projects_id)
        if project is None or project.status == Status.DELETED.code:
            raise NotFoundError(f"Project {projects_id} not found", field="projects_id")
        return project

    def create_project(self, name: str | None, project_type: str = ProjectType.AUDIO, description: str = "",
                       users_id: int | None = None) -> dict:
        try:
            project_type = Validation.require_choice(project_type, ProjectType.ALL, "project_type")
            with transaction() as session:
                project = Project(name=Validation.require_name(name), project_type=project_type, description=description,
                                  users_id=users_id)
                session.add(project)
                session.flush()
                logger.info(f"Created project {project.projects_id}")
                return self.to_dict(project)
        except Exception as exc:
            raise service_error(exc, "project_service.create_project")

    def list_projects(self, users_id: int | None = None, limit: int = 200) -> list[dict]:
        try:
            with read_session() as session:
                query = select(Project).where(Project.status != Status.DELETED.code)
                if users_id is not None:
                    query = query.where(Project.users_id == users_id)
                rows = session.scalars(query.order_by(Project.updated_at.desc()).limit(limit))
                return [self.to_dict(p) for p in rows]
        except Exception as exc:
            raise service_error(exc, "project_service.list_projects")

    def get(self, projects_id: int) -> dict:
        try:
            with read_session() as session:
                return self.to_dict(self._get(session, projects_id))
        except Exception as exc:
            raise service_error(exc, "project_service.get")

    def open_project(self, projects_id: int) -> dict:
        """Everything the Studio needs: project, scripts, audio and voices in use."""
        try:
            data = self.get(projects_id)
            data["scripts"] = [script_service.get(s["scripts_id"]) for s in script_service.list_scripts(projects_id)]
            data["audios"] = audio_service.list_audios(projects_id=projects_id, limit=500)
            voice_ids = {v for s in data["scripts"] for v in (s["speaker_map"] or {}).values()}
            voice_ids |= {sec["voices_id"] for s in data["scripts"] for sec in s["sections"] if sec["voices_id"]}
            data["voices_ids"] = sorted(voice_ids)
            data["takes"] = sum(len(sec["takes"]) for s in data["scripts"] for sec in s["sections"])
            return data
        except Exception as exc:
            raise service_error(exc, "project_service.open_project")

    def save_project(self, projects_id: int, edit_state: dict | None = None, settings: dict | None = None,
                     description: str | None = None) -> dict:
        """Persist editor/timeline state (used by autosave)."""
        try:
            with transaction() as session:
                project = self._get(session, projects_id)
                if edit_state is not None:
                    project.edit_state = edit_state
                if settings is not None:
                    project.settings = {**(project.settings or {}), **settings}
                if description is not None:
                    project.description = description
                project.updated_at = utcnow()
                return self.to_dict(project)
        except Exception as exc:
            raise service_error(exc, "project_service.save_project")

    def save(self, body: ProjectRequest) -> dict:
        """One entry point: create (no id), delete (status = Deleted) or update."""
        try:
            projects_id = body.projects_id
            if projects_id is None:
                created = self.create_project(body.name, body.project_type or ProjectType.AUDIO, body.description or "",
                                              body.users_id)
                projects_id = created["projects_id"]
            elif body.status == Status.DELETED.code:
                self.delete_project(projects_id)
                return deleted_result("projects_id", projects_id)
            else:
                self.update_project(projects_id, body.name, body.project_type, body.description)
            if body.edit_state is not None or body.settings is not None:
                self.save_project(projects_id, edit_state=body.edit_state, settings=body.settings)
            return self.get(projects_id)
        except Exception as exc:
            raise service_error(exc, "project_service.save")

    def save_edit_ops(self, projects_id: int, audios_id: int, ops: list[dict]) -> None:
        """Persist the editor's non-destructive edit list for one audio (autosave)."""
        try:
            with transaction() as session:
                project = self._get(session, projects_id)
                state = json.loads(json.dumps(project.edit_state or {}))
                state.setdefault("editor", {})[str(audios_id)] = ops
                project.edit_state = state
        except Exception as exc:
            raise service_error(exc, "project_service.save_edit_ops")

    def load_edit_ops(self, projects_id: int | None, audios_id: int) -> list[dict]:
        try:
            if projects_id is None:
                return []
            try:
                return list((self.get(projects_id)["edit_state"] or {}).get("editor", {}).get(str(audios_id), []))
            except NotFoundError:
                return []
        except Exception as exc:
            raise service_error(exc, "project_service.load_edit_ops")

    def rename_project(self, projects_id: int, name: str) -> dict:
        try:
            with transaction() as session:
                project = self._get(session, projects_id)
                project.name = Validation.require_name(name)
                return self.to_dict(project)
        except Exception as exc:
            raise service_error(exc, "project_service.rename_project")

    def update_project(self, projects_id: int, name: str | None = None, project_type: str | None = None,
                       description: str | None = None) -> dict:
        try:
            with transaction() as session:
                project = self._get(session, projects_id)
                if name is not None:
                    project.name = Validation.require_name(name)
                if project_type is not None:
                    project.project_type = Validation.require_choice(project_type, ProjectType.ALL, "project_type")
                if description is not None:
                    project.description = description
                return self.to_dict(project)
        except Exception as exc:
            raise service_error(exc, "project_service.update_project")

    def delete_project(self, projects_id: int) -> None:
        """Delete the project, its scripts/takes and all of its audio files."""
        try:
            with transaction() as session:
                project = self._get(session, projects_id)
                audios = session.scalars(select(Audio).where(Audio.projects_id == projects_id)).all()
                paths = [p for a in audios for p in (a.path, a.original_path) if p]
                # Delete children explicitly (and flush) before the project so the ORM and the
                # database-level ON DELETE CASCADE don't both try to remove the same rows.
                for script in session.scalars(select(Script).where(Script.projects_id == projects_id)):
                    session.delete(script)
                session.flush()
                for audio in audios:
                    session.delete(audio)
                session.flush()
                session.delete(project)
            for path in set(paths):
                remove_file(path)
            logger.info(f"Deleted project {projects_id}")
        except Exception as exc:
            raise service_error(exc, "project_service.delete_project")

    def duplicate_project(self, projects_id: int, name: str | None = None) -> dict:
        """Copy the project, its scripts, sections, takes and audio files."""
        try:
            with transaction() as session:
                source = self._get(session, projects_id)
                copy = Project(name=Validation.require_name(name or f"{source.name} (copy)"), project_type=source.project_type,
                               description=source.description, settings=dict(source.settings or {}),
                               edit_state=json.loads(json.dumps(source.edit_state or {})))
                session.add(copy)
                session.flush()

                audio_map: dict[int, int] = {}
                for audio in session.scalars(select(Audio).where(Audio.projects_id == projects_id)):
                    new_path = copy_file(audio.path, unique_path(subdir("audio"), audio.name, extension(audio.path)))
                    clone = Audio(**{c.key: getattr(audio, c.key) for c in Audio.__table__.columns
                                     if c.key not in ("audios_id", "created_at", "updated_at")})
                    clone.path, clone.projects_id, clone.original_path = str(new_path), copy.projects_id, None
                    session.add(clone)
                    session.flush()
                    audio_map[audio.audios_id] = clone.audios_id

                for script in session.scalars(select(Script).where(Script.projects_id == projects_id)):
                    new_script = Script(projects_id=copy.projects_id, title=script.title, body=script.body,
                                        speaker_map=dict(script.speaker_map or {}), settings=dict(script.settings or {}),
                                        final_audios_id=audio_map.get(script.final_audios_id)
                                        if script.final_audios_id else None)
                    for section in script.sections:
                        fields = {k: getattr(section, k) for k in ("position", "chapter", "heading", "speaker", "text",
                                                                   "voices_id", "speed", "pitch", "emotion", "style",
                                                                   "pause_after_ms")}
                        new_section = ScriptSection(**fields)
                        for take in section.takes:
                            if take.audios_id in audio_map:
                                new_section.takes.append(Take(audios_id=audio_map[take.audios_id],
                                                              take_number=take.take_number, selected=take.selected))
                        new_script.sections.append(new_section)
                    session.add(new_script)
                session.flush()
                logger.info(f"Duplicated project {projects_id} -> {copy.projects_id}")
                return self.to_dict(copy)
        except Exception as exc:
            raise service_error(exc, "project_service.duplicate_project")

    def export_project(self, projects_id: int, dest: str | Path | None = None) -> str:
        """Zip the project metadata and its audio files."""
        try:
            project = self.open_project(projects_id)
            dest = Path(dest) if dest else unique_path(subdir("exports"), project["name"], "zip")
            if dest.suffix.lower() != ".zip":
                dest = dest.with_suffix(".zip")
            dest.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                files = {}
                for audio in project["audios"]:
                    if Path(audio["path"]).exists():
                        arcname = f"audio/{audio['audios_id']}_{safe_name(audio['name'])}.{audio['format']}"
                        archive.write(audio["path"], arcname)
                        files[audio["audios_id"]] = arcname
                manifest = {
                    "voxlabs_project": 1,
                    "notice": f"Audio marked ai_generated=true is {AI_GENERATED_TAG}.",
                    "project": {k: v for k, v in project.items() if k not in ("audios", "scripts")},
                    "scripts": project["scripts"],
                    "audios": [{**{k: v for k, v in a.items() if k not in ("path", "original_path")},
                                "file": files.get(a["audios_id"])} for a in project["audios"]],
                }
                archive.writestr("project.json", json.dumps(manifest, indent=2, default=str))
            logger.info(f"Exported project {projects_id}")
            return str(dest)
        except Exception as exc:
            raise service_error(exc, "project_service.export_project")

    def ensure_exists(self, projects_id: int | None) -> None:
        try:
            if projects_id is not None:
                try:
                    self.get(projects_id)
                except NotFoundError as exc:
                    raise ProjectError(exc.message, field="projects_id") from exc
        except Exception as exc:
            raise service_error(exc, "project_service.ensure_exists")


project_service = ProjectService()
