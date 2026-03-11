"""Auth schemas."""
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenPayload(BaseModel):
    sub: str
    type: str  # dealer, admin
    id: int
    exp: int | None = None


class PasswordReset(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class DealerRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    customer_number: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=255)
    notes: str | None = Field(default=None, max_length=1000)


class DealerRegisterResponse(BaseModel):
    message: str
