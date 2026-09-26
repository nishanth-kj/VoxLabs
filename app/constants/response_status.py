from app.constants.base_enum import BaseEnum


class ResponseStatus(BaseEnum):
    """`status` field of every REST API response envelope."""

    SUCCESS = (1, "Success")
    ERROR = (0, "Error")
