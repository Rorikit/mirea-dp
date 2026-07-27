from enum import StrEnum


class EventStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class UserRole(StrEnum):
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"


class PresenceStatus(StrEnum):
    OUTSIDE = "OUTSIDE"
    INSIDE = "INSIDE"


class QrPurpose(StrEnum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class QrStatus(StrEnum):
    ACTIVE = "ACTIVE"
    USED = "USED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class AttendanceType(StrEnum):
    ENTRY = "ENTRY"
    EXIT = "EXIT"


class ImportStatus(StrEnum):
    UPLOADED = "UPLOADED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    READY_TO_CONFIRM = "READY_TO_CONFIRM"
    CONFIRMED = "CONFIRMED"
    APPLIED = "APPLIED"
    REJECTED = "REJECTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ImportAction(StrEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    UNCHANGED = "UNCHANGED"
    DEACTIVATE = "DEACTIVATE"
    ERROR = "ERROR"


class ValidationStatus(StrEnum):
    VALID = "VALID"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ErrorSeverity(StrEnum):
    ERROR = "ERROR"
    WARNING = "WARNING"
