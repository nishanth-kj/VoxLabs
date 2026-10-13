from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class Export(Base):
    """A file written by Export: where it went and what it was made from.

    The file belongs to the user once exported (it may be moved or deleted outside VoxLabs), so the row
    outlives both the file and its source audio; the Exports page shows which files are still there.
    """

    __tablename__ = "exports"

    exports_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audios_id: Mapped[int | None] = mapped_column(ForeignKey("audios.audios_id", ondelete="SET NULL"), index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    path: Mapped[str] = mapped_column(String(500))
    format: Mapped[str] = mapped_column(String(10), default="wav")
    sample_rate: Mapped[int] = mapped_column(Integer, default=0)
    duration: Mapped[float] = mapped_column(Float, default=0.0)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[int] = mapped_column(Integer, default=Status.ACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)
