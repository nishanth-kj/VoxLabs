"""Dubbing project and segment models for synchronized video dubbing."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class DubbingProject(Base):
    __tablename__ = "dubbing_projects"

    dubbing_projects_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200))
    source_media_path: Mapped[str] = mapped_column(String(500))
    source_audio_id: Mapped[int | None] = mapped_column(ForeignKey("audios.audios_id", ondelete="SET NULL"), nullable=True)
    target_audio_id: Mapped[int | None] = mapped_column(ForeignKey("audios.audios_id", ondelete="SET NULL"), nullable=True)
    output_video_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_language: Mapped[str] = mapped_column(String(20), default="en")
    target_language: Mapped[str] = mapped_column(String(20), default="en")
    speaker_map: Mapped[dict] = mapped_column(JSON, default=dict)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    video_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    video_fps: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    segments = relationship(
        "DubbingSegment", back_populates="project", cascade="all, delete-orphan", order_by="DubbingSegment.position"
    )


class DubbingSegment(Base):
    __tablename__ = "dubbing_segments"

    dubbing_segments_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dubbing_projects_id: Mapped[int] = mapped_column(ForeignKey("dubbing_projects.dubbing_projects_id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    start_ms: Mapped[int] = mapped_column(Integer, default=0, index=True)
    end_ms: Mapped[int] = mapped_column(Integer, default=0)
    speaker: Mapped[str] = mapped_column(String(80), default="Narrator")
    source_text: Mapped[str] = mapped_column(Text, default="")
    target_text: Mapped[str] = mapped_column(Text, default="")
    voices_id: Mapped[int | None] = mapped_column(ForeignKey("voices.voices_id", ondelete="SET NULL"), nullable=True)
    audios_id: Mapped[int | None] = mapped_column(ForeignKey("audios.audios_id", ondelete="SET NULL"), nullable=True)
    generated_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    pitch: Mapped[float | None] = mapped_column(Float, nullable=True)
    emotion: Mapped[str | None] = mapped_column(String(20), nullable=True)
    locked: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    project = relationship("DubbingProject", back_populates="segments")

