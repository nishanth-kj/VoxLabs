from typing import Any

from fastapi.responses import JSONResponse

from app.constants.response_status import ResponseStatus
from app.exceptions import AppError
from app.models.response.error_detail import ErrorDetail
from app.utils.validation import Validation


class ApiResponse(JSONResponse):
    """Envelope for every API response, always HTTP 200. Routes return it directly.

        ApiResponse(data).success()
        -> {"status": 1, "data": [...], "error": null}

        ApiResponse(error=NotFoundError("Voice 42 not found", field="voices_id")).error()
        -> {"status": 0, "data": null, "error": {"error_code": 404,
            "error_message": "The requested item was not found.",
            "field": {"voices_id": "Voice 42 not found"}}}
    """

    def __init__(self, data: Any = None, error: AppError | None = None):
        # The response body is rendered by success() / error().
        self.data = data
        self.exception = error

    def success(self) -> "ApiResponse":
        return self._respond(ResponseStatus.SUCCESS.code, Validation.response_data(self.data), None)

    def error(self) -> "ApiResponse":
        exc = self.exception or AppError()
        if isinstance(exc.field, dict):
            fields = exc.field or None
        else:
            fields = {exc.field: exc.message} if exc.field else None
        detail = ErrorDetail(
            error_code=exc.error_code.code,
            error_message=exc.error_message.value,
            field=fields,
        )
        return self._respond(ResponseStatus.ERROR.code, None, detail.model_dump())

    def _respond(self, status: int, data: Any, error: dict | None) -> "ApiResponse":
        super().__init__(content={"status": status, "data": data, "error": error}, status_code=200)
        return self
