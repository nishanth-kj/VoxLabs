from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class ScriptSection(Base):
    """One generatable unit of a script: a paragraph or a speaker's line."""

    __tablename__ = "script_sections"

    script_sections_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scripts_id: Mapped[int] = mapped_column(ForeignKey("scripts.scripts_id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer, default=0)
    chapter: Mapped[str] = mapped_column(String(200), default="")
    heading: Mapped[str] = mapped_column(String(200), default="")
    speaker: Mapped[str] = mapped_column(String(80), default="")
    text: Mapped[str] = mapped_column(Text)
    # Per-section overrides; NULL means "use the script / speaker default".
    voices_id: Mapped[int | None] = mapped_column(ForeignKey("voices.voices_id", ondelete="SET NULL"))
    speed: Mapped[float | None] = mapped_column(Float)
    pitch: Mapped[float | None] = mapped_column(Float)
    emotion: Mapped[str | None] = mapped_column(String(20))
    style: Mapped[str | None] = mapped_column(String(30))
    pause_after_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)

    script = relationship("Script", back_populates="sections")
    takes = relationship("Take", back_populates="section", cascade="all, delete-orphan", order_by="Take.take_number")
