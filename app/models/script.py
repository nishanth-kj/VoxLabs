from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class Script(Base):
    __tablename__ = "scripts"

    scripts_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    projects_id: Mapped[int | None] = mapped_column(ForeignKey("projects.projects_id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text, default="")
    # {"Teacher": voices_id, ...}; "*" is the default narrator voice.
    speaker_map: Mapped[dict] = mapped_column(JSON, default=dict)
    # Defaults applied to sections without their own settings, plus intro/outro text.
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    final_audios_id: Mapped[int | None] = mapped_column(ForeignKey("audios.audios_id", ondelete="SET NULL"))
    status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)

    sections = relationship(
        "ScriptSection", back_populates="script", cascade="all, delete-orphan", order_by="ScriptSection.position"
    )
