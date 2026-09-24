"""`Status`: the only constant used by the `status` column of every table.

Columns store the integer code (`default=Status.ACTIVE.code`). A table that
needs its own numbered state gets a separate `<name>_status` column with its
own BaseEnum in its own file (e.g. `voices.consent_status` → ConsentStatus).
"""

from app.constants.base_enum import BaseEnum


class Status(BaseEnum):
    ACTIVE = (1, "Active")
    INACTIVE = (2, "Inactive")
    PENDING = (3, "Pending")
    IN_PROGRESS = (4, "InProgress")
    COMPLETED = (5, "Completed")
    FAILED = (6, "Failed")
    CANCELLED = (7, "Cancelled")
    DELETED = (8, "Deleted")
