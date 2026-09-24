"""Lightweight application exceptions.

Each class maps to a predefined `ErrorCode` and `ErrorMessage`. Services
raise them with a specific `message` and optional `field`; the UI shows the
message and the API returns everything in the error envelope.
"""

from app.constants.error_code import ErrorCode
from app.constants.error_message import ErrorMessage
from app.utils.logger import logger


class AppError(Exception):
    error_code = ErrorCode.BAD_REQUEST
    error_message = ErrorMessage.BAD_REQUEST

    def __init__(self, message: str | None = None, field: str | dict[str, str] | None = None):
        """`field` is the offending input name, or a {field: message} dict for several at once."""
        self.message = message or self.error_message.value
        self.field = field
        self.logged = False
        super().__init__(self.message)


class ValidationError(AppError):
    error_code = ErrorCode.VALIDATION_ERROR
    error_message = ErrorMessage.VALIDATION_ERROR


class NotFoundError(AppError):
    error_code = ErrorCode.NOT_FOUND
    error_message = ErrorMessage.NOT_FOUND


class AuthError(AppError):
    error_code = ErrorCode.UNAUTHORIZED
    error_message = ErrorMessage.UNAUTHORIZED


class ConsentError(AppError):
    error_code = ErrorCode.CONSENT_REQUIRED
    error_message = ErrorMessage.CONSENT_REQUIRED


class VoiceError(AppError):
    """The voice exists but can't be used this way (revoked, preset without samples...)."""

    error_code = ErrorCode.CONFLICT
    error_message = ErrorMessage.CONFLICT


class AudioError(AppError):
    error_code = ErrorCode.BAD_REQUEST
    error_message = ErrorMessage.BAD_REQUEST


class ModelError(AppError):
    """The model is not installed, not allowed (online) or failed to load."""

    error_code = ErrorCode.SERVICE_UNAVAILABLE
    error_message = ErrorMessage.SERVICE_UNAVAILABLE


class JobError(AppError):
    error_code = ErrorCode.CONFLICT
    error_message = ErrorMessage.CONFLICT


class ProjectError(AppError):
    error_code = ErrorCode.BAD_REQUEST
    error_message = ErrorMessage.BAD_REQUEST


class InternalError(AppError):
    error_code = ErrorCode.INTERNAL_SERVER_ERROR
    error_message = ErrorMessage.INTERNAL_SERVER_ERROR


class JobCancelled(AppError):
    """Raised inside a background job once cancel() was requested; JobService marks the job Cancelled."""

    error_code = ErrorCode.CONFLICT
    error_message = ErrorMessage.CONFLICT


def service_error(exc: Exception, action: str) -> AppError:
    """Log a failed service call once and return it as an AppError to raise.

    Services wrap their public methods in `try: ... except Exception as exc: raise service_error(exc, "...")`.
    AppErrors pass through unchanged (logged as warnings); anything unexpected is logged with its
    traceback and replaced by InternalError, so callers never see raw library exceptions.
    """
    if isinstance(exc, JobCancelled):
        return exc
    if isinstance(exc, AppError):
        if not exc.logged:
            logger.warning(f"{action}: {exc.message}")
            exc.logged = True
        return exc
    logger.error(f"{action} failed: {exc}", exc_info=exc)
    error = InternalError()
    error.logged = True
    error.__cause__ = exc
    return error
