from pydantic import BaseModel
from typing import Any, Optional


class ErrorDetail(BaseModel):
    """Structured error payload"""
    code: int
    message: str
    field: Optional[Any] = None
