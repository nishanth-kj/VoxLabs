from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.project_type import ProjectType
from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class Project(Base):
    __tablename__ = "projects"

    projects_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    users_id: Mapped[int | None] = mapped_column(ForeignKey("users.users_id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    project_type: Mapped[str] = mapped_column(String(20), default=ProjectType.AUDIO)
    description: Mapped[str] = mapped_column(Text, default="")
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    # Non-destructive editor state: {"audios_id": {"ops": [...]}}, timeline, etc.
    edit_state: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)
