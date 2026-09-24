"""UserService: local user profiles (who owns voices, projects and consent records)."""

import re

from sqlalchemy import select

from app.constants.status import Status
from app.exceptions import NotFoundError, ValidationError, service_error
from app.models import Job, User
from app.models.request import UserRequest
from app.services.job_service import job_service
from app.services.voice_service import voice_service
from app.utils.database import deleted_result, read_session, serialize, transaction
from app.utils.logger import logger
from app.utils.validation import Validation

_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserService:
    def to_dict(self, user: User) -> dict:
        return serialize(user)

    def validate_user(self, name: str | None, email: str | None = None) -> tuple[str, str | None]:
        name = Validation.require_name(name)
        email = (email or "").strip() or None
        if email and not _EMAIL.match(email):
            raise ValidationError("Invalid email address", field="email")
        return name, email

    def _get(self, session, users_id: int) -> User:
        user = session.get(User, users_id)
        if user is None or user.status == Status.DELETED.code:
            raise NotFoundError(f"User {users_id} not found", field="users_id")
        return user

    def create_user(self, name: str | None, email: str | None = None) -> dict:
        try:
            name, email = self.validate_user(name, email)
            with transaction() as session:
                if email and session.scalar(select(User).where(User.email == email)):
                    raise ValidationError("A user with this email already exists", field="email")
                user = User(name=name, email=email)
                session.add(user)
                session.flush()
                logger.info(f"Created user {user.users_id}")
                return self.to_dict(user)
        except Exception as exc:
            raise service_error(exc, "user_service.create_user")

    def get_user(self, users_id: int) -> dict:
        try:
            with read_session() as session:
                return self.to_dict(self._get(session, users_id))
        except Exception as exc:
            raise service_error(exc, "user_service.get_user")

    def list_users(self) -> list[dict]:
        try:
            with read_session() as session:
                return [self.to_dict(u) for u in session.scalars(
                    select(User).where(User.status != Status.DELETED.code).order_by(User.name))]
        except Exception as exc:
            raise service_error(exc, "user_service.list_users")

    def update_user(self, users_id: int, name: str | None = None, email: str | None = None) -> dict:
        try:
            with transaction() as session:
                user = self._get(session, users_id)
                new_name, new_email = self.validate_user(name or user.name,
                                                         email if email is not None else user.email)
                user.name, user.email = new_name, new_email
                logger.info(f"Updated user {users_id}")
                return self.to_dict(user)
        except Exception as exc:
            raise service_error(exc, "user_service.update_user")

    def delete_user(self, users_id: int) -> None:
        try:
            with transaction() as session:
                session.delete(self._get(session, users_id))
            logger.info(f"Deleted user {users_id}")
        except Exception as exc:
            raise service_error(exc, "user_service.delete_user")

    def save(self, body: UserRequest) -> dict:
        """One entry point: create (no id), delete (status = Deleted) or update."""
        try:
            if body.users_id is None:
                return self.create_user(body.name, body.email)
            if body.status == Status.DELETED.code:
                self.delete_user(body.users_id)
                return deleted_result("users_id", body.users_id)
            return self.update_user(body.users_id, body.name, body.email)
        except Exception as exc:
            raise service_error(exc, "user_service.save")

    def get_user_voices(self, users_id: int) -> list[dict]:
        try:
            self.get_user(users_id)
            return voice_service.list_voices(users_id=users_id)
        except Exception as exc:
            raise service_error(exc, "user_service.get_user_voices")

    def get_user_projects(self, users_id: int) -> list[dict]:
        from app.services.project_service import project_service

        try:
            self.get_user(users_id)
            return project_service.list_projects(users_id=users_id)
        except Exception as exc:
            raise service_error(exc, "user_service.get_user_projects")

    def get_user_jobs(self, users_id: int) -> list[dict]:
        try:
            self.get_user(users_id)
            with read_session() as session:
                rows = session.scalars(
                    select(Job).where(Job.users_id == users_id).order_by(Job.created_at.desc()).limit(50))
                return [job_service.to_dict(j) for j in rows]
        except Exception as exc:
            raise service_error(exc, "user_service.get_user_jobs")


user_service = UserService()
