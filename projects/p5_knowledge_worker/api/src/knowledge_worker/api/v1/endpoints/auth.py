"""Sign-up, sign-in and current-user endpoints."""

from fastapi import APIRouter, Request, status

from knowledge_worker.api.deps import ContainerDep, CurrentUserIdDep, SettingsDep, UserServiceDep
from knowledge_worker.core.exceptions import NotFoundError, UnauthorizedError
from knowledge_worker.core.security import create_access_token
from knowledge_worker.db.models import UserModel
from knowledge_worker.schemas.auth import (
    AuthConfig,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserOut,
)

router = APIRouter()


def _token_for(user: UserModel, settings: SettingsDep) -> TokenResponse:
    token = create_access_token(user.id, settings.SECRET_KEY, settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return TokenResponse(
        access_token=token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=UserOut.model_validate(user),
    )


@router.get("/config", response_model=AuthConfig, summary="Whether sign-in is required")
def auth_config(settings: SettingsDep) -> AuthConfig:
    return AuthConfig(
        enabled=settings.AUTH_ENABLED,
        demo_login_enabled=settings.AUTH_ENABLED and settings.is_local,
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
    description="Creates the account and signs it in, so the response already carries a token.",
)
def register(payload: RegisterRequest, users: UserServiceDep, settings: SettingsDep) -> TokenResponse:
    user = users.register(payload.email, payload.name, payload.password)
    return _token_for(user, settings)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Sign in",
    description="After repeated failures the client gets 429 with a Retry-After header.",
)
def login(
    payload: LoginRequest,
    request: Request,
    users: UserServiceDep,
    settings: SettingsDep,
    container: ContainerDep,
) -> TokenResponse:
    limiter = container.login_limiter
    # The socket address, not X-Forwarded-For: that header is client-controlled unless a
    # trusted proxy sets it.
    ip = request.client.host if request.client else "unknown"
    limiter.check(ip, payload.email)  # blocked even if this attempt's password is right
    try:
        user = users.authenticate(payload.email, payload.password)
    except UnauthorizedError:
        limiter.record_failure(ip, payload.email)
        raise
    limiter.reset(ip, payload.email)
    return _token_for(user, settings)


@router.post("/demo", response_model=TokenResponse, summary="Sign in to the local demo account")
def demo_login(users: UserServiceDep, settings: SettingsDep) -> TokenResponse:
    if not settings.AUTH_ENABLED or not settings.is_local:
        raise NotFoundError("Demo login is only available in local development.")
    return _token_for(users.get_or_create_demo_user(), settings)


@router.get("/me", response_model=UserOut, summary="The signed-in user")
def me(user_id: CurrentUserIdDep, users: UserServiceDep) -> UserOut:
    user = users.get(user_id)
    if user is None:  # only reachable with AUTH_ENABLED=false, where there is no account
        raise NotFoundError("Sign-in is disabled, so there is no account.")
    return UserOut.model_validate(user)
