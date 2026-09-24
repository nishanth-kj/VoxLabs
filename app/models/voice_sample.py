from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class VoiceSample(Base):
    __tablename__ = "voice_samples"

    voice_samples_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voices_id: Mapped[int] = mapped_column(ForeignKey("voices.voices_id", ondelete="CASCADE"), index=True)
    path: Mapped[str] = mapped_column(String(500))
    original_name: Mapped[str] = mapped_column(String(255), default="")
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    sample_rate: Mapped[int] = mapped_column(Integer, default=0)
    quality: Mapped[dict] = mapped_column(JSON, default=dict)
    sha256: Mapped[str] = mapped_column(String(64), default="")
    status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)

    voice = relationship("Voice", back_populates="samples")
