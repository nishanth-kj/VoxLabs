from app.constants.base_enum import BaseEnum


class ConsentStatus(BaseEnum):
    """`voices.consent_status`: whether cloning permission is on record."""

    NOT_REQUIRED = (1, "NotRequired")  # preset engine voices, nobody is cloned
    GRANTED = (2, "Granted")
    REVOKED = (3, "Revoked")
