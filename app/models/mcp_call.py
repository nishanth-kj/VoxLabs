from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.status import Status
from app.utils.database import Base
from app.utils.time import utcnow


class McpCall(Base):
    """One MCP tool call: which tool, over which transport, with what arguments, and how it ended.

    MCP clients often run VoxLabs in their own process (stdio), so the log lives in the database, where the
    desktop app's MCP page can read it. `status` is Status.COMPLETED or Status.FAILED.
    """

    __tablename__ = "mcp_calls"

    mcp_calls_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tool: Mapped[str] = mapped_column(String(100), index=True)
    transport: Mapped[str] = mapped_column(String(10), default="http")
    arguments: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict | None] = mapped_column(JSON)
    error: Mapped[str | None] = mapped_column(String(1000))
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[int] = mapped_column(Integer, default=Status.COMPLETED.code, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow,
                                                 nullable=False)
