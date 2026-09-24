from app.constants.base_enum import BaseEnum


class ErrorCode(BaseEnum):
    """API error codes (HTTP meanings): `.code` is the `error_code`, `.value` the error `type`.

    The HTTP status of the response itself is always 200.
    """

    BAD_REQUEST = (400, "BadRequest")
    UNAUTHORIZED = (401, "Unauthorized")
    CONSENT_REQUIRED = (403, "ConsentRequired")
    NOT_FOUND = (404, "NotFound")
    CONFLICT = (409, "Conflict")
    VALIDATION_ERROR = (422, "ValidationError")
    INTERNAL_SERVER_ERROR = (500, "InternalServerError")
    SERVICE_UNAVAILABLE = (503, "ServiceUnavailable")
