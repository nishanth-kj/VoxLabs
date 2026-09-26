from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class Audio(Base):
    """An audio file on disk. `path` is what plays; `original_path` is kept untouched."""

    __tablename__ = "audios"

    audios_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    projects_id: Mapped[int | None] = mapped_column(ForeignKey("projects.projects_id", ondelete="SET NULL"), index=True)
    parent_audios_id: Mapped[int | None] = mapped_column(ForeignKey("audios.audios_id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), default="")
    path: Mapped[str] = mapped_column(String(500))
    original_path: Mapped[str | None] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(20))
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    sample_rate: Mapped[int] = mapped_column(Integer, default=0)
    channels: Mapped[int] = mapped_column(Integer, default=1)
    format: Mapped[str] = mapped_column(String(10), default="wav")
    codec: Mapped[str | None] = mapped_column(String(40))
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    loudness: Mapped[float | None] = mapped_column(Float)
    # Generation / processing parameters (text, voice, model, steps...).
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)
