from typing import Any

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel

from app.constants.response_status import ResponseStatus
from app.models.response.error_detail import ErrorDetail


class ApiResponse(BaseModel):
    """Envelope for every API response (always HTTP 200): {"status": 1|0, "data": ..., "error": null|str}."""

    status: int = ResponseStatus.SUCCESS.code
    data: Any = None
    error: str | None = None

    @classmethod
    def success(cls, data: Any = None) -> "ApiResponse":
        return cls(status=ResponseStatus.SUCCESS.code, data=jsonable_encoder(data))

    @classmethod
    def failure(cls, message: str, error_type: str = "Error", field: str | None = None) -> "ApiResponse":
        detail = ErrorDetail(type=error_type, field=field)
        return cls(status=ResponseStatus.ERROR.code, data=detail.model_dump(), error=message)
