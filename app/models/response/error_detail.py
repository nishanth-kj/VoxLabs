from pydantic import BaseModel


class ErrorDetail(BaseModel):
    """`data` of a failed ApiResponse: the error class name and the offending field, if any."""

    type: str
    field: str | None = None
