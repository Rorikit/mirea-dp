from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.enums import UserRole


class ImportConfirmRequest(BaseModel):
    preview_version: str
    accept_warnings: bool = False
    confirm_deactivations: bool = False
    confirmation_phrase: str | None = None


class CancelRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=500)


class UserCreateRequest(BaseModel):
    username: str = Field(pattern=r"^[a-zA-Z0-9_.-]{3,100}$")
    password: str = Field(min_length=12, max_length=256)
    role: UserRole = UserRole.OPERATOR


class UserPatchRequest(BaseModel):
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=256)


class StudentPatchRequest(BaseModel):
    is_active: bool | None = None


class ScheduleCreateRequest(BaseModel):
    event_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    location: str = Field(min_length=1, max_length=255)
    starts_at: datetime
    ends_at: datetime
    display_order: int = 0
    is_published: bool = False

    @field_validator("starts_at", "ends_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            raise ValueError("Время должно содержать часовой пояс")
        return value


class SchedulePatchRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    location: str | None = Field(default=None, min_length=1, max_length=255)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    display_order: int | None = None
    is_published: bool | None = None

    @field_validator("starts_at", "ends_at")
    @classmethod
    def require_optional_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("Время должно содержать часовой пояс")
        return value


class ArchiveEventRequest(BaseModel):
    confirmation_phrase: str
