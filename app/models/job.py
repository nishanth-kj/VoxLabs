from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class Job(Base):
    """A background task. `status`: Pending → InProgress → Completed | Failed | Cancelled."""

    __tablename__ = "jobs"

    jobs_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    users_id: Mapped[int | None] = mapped_column(ForeignKey("users.users_id", ondelete="SET NULL"), index=True)
    job_type: Mapped[str] = mapped_column(String(40), index=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    error: Mapped[str | None] = mapped_column(Text)
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[int] = mapped_column(Integer, default=Status.PENDING.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)
