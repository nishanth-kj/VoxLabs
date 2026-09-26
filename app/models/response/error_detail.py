from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """The `error` object of a failed ApiResponse."""

    error_code: int  # ErrorCode.code, e.g. 404
    error_message: str  # ErrorMessage.value, e.g. "The requested item was not found."
    field: dict[str, str] | None = None  # field name -> message, e.g. {"voices_id": "Voice 42 not found"}
