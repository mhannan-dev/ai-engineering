"""Authentication endpoints for user login and token generation."""

from fastapi import APIRouter

from meeting_intelligence.api.deps import SettingsDep, UserServiceDep
from meeting_intelligence.core.security import create_access_token
from meeting_intelligence.schemas.user import Token, UserLogin

router = APIRouter()


@router.post(
    "/login",
    response_model=Token,
    summary="User login",
    description="Authenticate with email and password to receive a bearer token.",
)
async def login(
    payload: UserLogin,
    user_service: UserServiceDep,
    settings: SettingsDep,
) -> Token:
    """Authenticate credentials and generate access token."""
    user = user_service.authenticate_user(payload.email, payload.password)
    access_token = create_access_token(
        subject=user.id,
        secret_key=settings.SECRET_KEY,
        expires_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
