"""User and authentication schemas."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Payload for registering a new user."""

    email: EmailStr = Field(description="User primary email address.")
    password: str = Field(min_length=8, description="User password (min 8 chars).")
    first_name: str = Field(description="User first name.")
    last_name: str | None = Field(default=None, description="User last name.")
    subscription_tier: str | None = Field(default="free", description="Subscription tier.")


class UserLogin(BaseModel):
    """Payload for user authentication."""

    email: EmailStr = Field(description="User email address.")
    password: str = Field(description="User password.")


class UserUpdate(BaseModel):
    """Payload for updating user profile information."""

    first_name: str | None = Field(default=None, description="User first name.")
    last_name: str | None = Field(default=None, description="User last name.")


class UserRead(BaseModel):
    """Serialized user representation for public consumption."""

    id: str
    email: EmailStr
    first_name: str
    last_name: str | None = None
    avatar: str | None = None
    subscription_tier: str = "free"
    is_active: bool = True
    created_at: datetime


class Token(BaseModel):
    """JWT authorization token returned upon successful login."""

    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class TokenPayload(BaseModel):
    """Decoded access token claims."""

    sub: str
    exp: int
    iat: int
