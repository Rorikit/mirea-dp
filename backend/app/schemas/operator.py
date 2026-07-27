from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import AttendanceType, PresenceStatus


class ScanRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)
    device_info: dict[str, Any] | None = None


class ScanResponse(BaseModel):
    result: str
    full_name: str
    study_group: str
    institute: str
    event_type: AttendanceType
    previous_status: PresenceStatus
    new_status: PresenceStatus
    occurred_at: datetime
    request_id: UUID
