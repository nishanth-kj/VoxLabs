"""Lightweight application exceptions.

Services raise these. The UI shows `message` in a dialog; the API returns it in
the ApiResponse envelope (HTTP 200, status 0, `data.type` = class name).
Internal details never leak to users or clients.
"""


class AppError(Exception):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field


class ValidationError(AppError):
    pass


class NotFoundError(AppError):
    pass


class ConsentError(AppError):
    pass


class AuthError(AppError):
    pass


class VoiceError(AppError):
    pass


class AudioError(AppError):
    pass


class ModelError(AppError):
    pass


class JobError(AppError):
    pass


class ProjectError(AppError):
    pass
