from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import PresenceStatus, QrPurpose


class RegistrationLookupRequest(BaseModel):
    event_slug: str = Field(min_length=1, max_length=100)
    full_name: str = Field(min_length=2, max_length=300)
    study_group: str = Field(min_length=1, max_length=100)


class LookupResponse(BaseModel):
    match: str = "FOUND"
    lookup_token: str
    expires_at: datetime


class RegistrationCreateRequest(BaseModel):
    lookup_token: str


class QrResponse(BaseModel):
    token: str
    purpose: QrPurpose
    expires_at: datetime


class StudentProfileResponse(BaseModel):
    public_id: UUID
    full_name: str
    study_group: str
    institute: str
    presence_status: PresenceStatus
    qr: QrResponse | None = None


class QrCreateRequest(BaseModel):
    purpose: QrPurpose = QrPurpose.ENTRY
