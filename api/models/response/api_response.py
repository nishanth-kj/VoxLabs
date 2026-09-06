from pydantic import BaseModel
from typing import Any, Optional

from .error_detail import ErrorDetail


class APIResponse(BaseModel):
    """Standardized API Response wrapper"""
    status: int
    data: Optional[Any] = None
    error: Optional[ErrorDetail] = None
