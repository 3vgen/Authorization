from pydantic import BaseModel, EmailStr
import uuid


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    is_active: bool
    is_verified: bool

    model_config = {"from_attributes": True}
