from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.consent_status import ConsentStatus
from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class Voice(Base):
    __tablename__ = "voices"

    voices_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    users_id: Mapped[int | None] = mapped_column(ForeignKey("users.users_id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(16), default="en")
    # Catalog key of the model that built this voice (clone) or speaks it (preset).
    model_key: Mapped[str | None] = mapped_column(String(80))
    # "clone" (from samples) or "preset" (an engine's built-in speaker, e.g. an Edge voice).
    source: Mapped[str] = mapped_column(String(20), default="clone")
    engine_voice: Mapped[str | None] = mapped_column(String(120))
    consent_status: Mapped[int] = mapped_column(Integer, default=ConsentStatus.GRANTED.code, nullable=False)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    storage_dir: Mapped[str | None] = mapped_column(String(500))
    sample_count: Mapped[int] = mapped_column(Integer, default=0)
    preview_audios_id: Mapped[int | None] = mapped_column(ForeignKey("audios.audios_id", ondelete="SET NULL"))
    status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)

    samples = relationship("VoiceSample", back_populates="voice", cascade="all, delete-orphan")
    consents = relationship("VoiceConsent", back_populates="voice", cascade="all, delete-orphan")
