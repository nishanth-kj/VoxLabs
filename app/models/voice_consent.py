from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class VoiceConsent(Base):
    """Audit record of who allowed a voice to be cloned.

    `status` is Active while consent stands and Inactive once revoked (`revoked_at` is set).
    """

    __tablename__ = "voice_consents"

    voice_consents_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voices_id: Mapped[int] = mapped_column(ForeignKey("voices.voices_id", ondelete="CASCADE"), index=True)
    granted_by: Mapped[str] = mapped_column(String(120))
    speaker_name: Mapped[str] = mapped_column(String(120))
    statement: Mapped[str] = mapped_column(Text)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)

    voice = relationship("Voice", back_populates="consents")
