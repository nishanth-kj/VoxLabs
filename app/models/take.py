from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class Take(Base):
    """One generated rendition of a script section. Only the selected take is rendered."""

    __tablename__ = "takes"

    takes_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    script_sections_id: Mapped[int] = mapped_column(
        ForeignKey("script_sections.script_sections_id", ondelete="CASCADE"), index=True
    )
    audios_id: Mapped[int] = mapped_column(ForeignKey("audios.audios_id", ondelete="CASCADE"))
    take_number: Mapped[int] = mapped_column(Integer, default=1)
    selected: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)

    section = relationship("ScriptSection", back_populates="takes")
