from __future__ import annotations
from pydantic import BaseModel, EmailStr


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None
    timezone: str = "UTC"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    is_verified: bool
    is_active: bool
    timezone: str

    model_config = {"from_attributes": True}