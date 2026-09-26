from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class Model(Base):
    """A known AI model. `status` is Active when installed and Inactive otherwise."""

    __tablename__ = "models"

    models_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(80), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    model_type: Mapped[str] = mapped_column(String(20))
    backend: Mapped[str] = mapped_column(String(30))
    version: Mapped[str] = mapped_column(String(30), default="")
    size_mb: Mapped[int] = mapped_column(Integer, default=0)
    vram_mb: Mapped[int] = mapped_column(Integer, default=0)
    capabilities: Mapped[list] = mapped_column(JSON, default=list)
    online: Mapped[bool] = mapped_column(Boolean, default=False)
    installed_path: Mapped[str | None] = mapped_column(String(500))
    device: Mapped[str] = mapped_column(String(20), default="cpu")
    status: Mapped[int] = mapped_column(Integer, default=Status.INACTIVE.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)
