from typing import Any, Optional
from constants.error_message import ErrorMessage


class ApiException(Exception):
    """
    Base runtime exception for API errors.

    Raise this (or a subclass) anywhere in a service/route to have
    ApiResponse.error() turn it into the standard {code, message, field}
    error payload.
    """

    def __init__(
        self,
        message: Optional[str] = None,
        code: int = ErrorMessage.INTERNAL_SERVER_ERROR.code,
        field: Optional[Any] = None,
    ):
        self.code = code
        self.message = message or ErrorMessage.INTERNAL_SERVER_ERROR.text
        self.field = field
        super().__init__(self.message)

    @classmethod
    def from_error_message(
        cls,
        error_message: ErrorMessage,
        message: Optional[str] = None,
        field: Optional[Any] = None,
    ) -> "ApiException":
        return cls(message=message or error_message.text, code=error_message.code, field=field)


class BadRequestException(ApiException):
    def __init__(self, message: Optional[str] = None, field: Optional[Any] = None):
        super().__init__(message or ErrorMessage.BAD_REQUEST.text, ErrorMessage.BAD_REQUEST.code, field)


class UnauthorizedException(ApiException):
    def __init__(self, message: Optional[str] = None, field: Optional[Any] = None):
        super().__init__(message or ErrorMessage.UNAUTHORIZED.text, ErrorMessage.UNAUTHORIZED.code, field)


class NotFoundException(ApiException):
    def __init__(self, message: Optional[str] = None, field: Optional[Any] = None):
        super().__init__(message or ErrorMessage.NOT_FOUND.text, ErrorMessage.NOT_FOUND.code, field)


class ValidationException(ApiException):
    def __init__(self, message: Optional[str] = None, field: Optional[Any] = None):
        super().__init__(message or ErrorMessage.VALIDATION_ERROR.text, ErrorMessage.VALIDATION_ERROR.code, field)


class InternalServerErrorException(ApiException):
    def __init__(self, message: Optional[str] = None, field: Optional[Any] = None):
        super().__init__(message or ErrorMessage.INTERNAL_SERVER_ERROR.text, ErrorMessage.INTERNAL_SERVER_ERROR.code, field)
