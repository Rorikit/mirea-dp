from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=12, max_length=256)


class UserResponse(BaseModel):
    id: UUID
    username: str
    role: UserRole

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    access_token: str
    expires_in: int
    csrf_token: str
    user: UserResponse
