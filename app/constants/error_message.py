from app.constants.base_enum import BaseEnum


class ErrorMessage(BaseEnum):
    """Predefined error text for each ErrorCode (same member names and codes).

    `.value` is sent as the response's `error_message`.
    """

    BAD_REQUEST = (400, "The request could not be processed.")
    UNAUTHORIZED = (401, "A valid API token is required.")
    CONSENT_REQUIRED = (403, "Explicit consent from the speaker is required.")
    NOT_FOUND = (404, "The requested item was not found.")
    CONFLICT = (409, "The item cannot be changed in its current state.")
    VALIDATION_ERROR = (422, "Some input values are invalid.")
    INTERNAL_SERVER_ERROR = (500, "Something went wrong. Please try again.")
    SERVICE_UNAVAILABLE = (503, "The selected model or engine is not available.")
