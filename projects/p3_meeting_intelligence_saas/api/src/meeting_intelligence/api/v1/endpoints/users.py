"""User management endpoints."""

from fastapi import APIRouter, File, UploadFile, status
from fastapi.concurrency import run_in_threadpool

from meeting_intelligence.api.deps import CurrentUserDep, SettingsDep, UserServiceDep
from meeting_intelligence.models.user import User
from meeting_intelligence.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter()


@router.post(
    "/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with unique email address.",
)
def create_user(payload: UserCreate, user_service: UserServiceDep) -> UserRead:
    """Register a new user account."""
    return _to_read(user_service.register_user(payload))


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    description="Retrieve the profile of the authenticated caller.",
)
def get_me(current_user: CurrentUserDep) -> UserRead:
    """Return authenticated caller's profile."""
    return _to_read(current_user)


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current user",
    description="Update the profile of the authenticated caller.",
)
def update_me(
    payload: UserUpdate, current_user: CurrentUserDep, user_service: UserServiceDep
) -> UserRead:
    """Update authenticated caller's profile."""
    user = user_service.update_user(
        user_id=current_user.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    return _to_read(user)


def _to_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar=user.avatar,
        subscription_tier=user.subscription_tier,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post(
    "/me/avatar",
    response_model=UserRead,
    summary="Upload avatar",
    description="Upload a JPG, JPEG, PNG or WEBP image (max 2 MB) as the caller's avatar; it is converted to WebP.",
)
async def upload_avatar(
    current_user: CurrentUserDep,
    user_service: UserServiceDep,
    settings: SettingsDep,
    file: UploadFile = File(..., description="Avatar image file."),
) -> UserRead:
    """Replace the authenticated caller's avatar image."""
    # Read one byte past the limit so oversized files are rejected without buffering them fully
    content = await file.read(settings.AVATAR_MAX_BYTES + 1)
    # Image conversion + DB writes are blocking; run them off the event loop
    user = await run_in_threadpool(
        user_service.update_avatar,
        current_user,
        content,
        settings.UPLOAD_DIR,
        settings.AVATAR_MAX_BYTES,
        original_filename=file.filename,
    )
    return _to_read(user)


@router.delete(
    "/me/avatar",
    response_model=UserRead,
    summary="Remove avatar",
    description="Delete the caller's avatar image.",
)
def delete_avatar(
    current_user: CurrentUserDep, user_service: UserServiceDep, settings: SettingsDep
) -> UserRead:
    """Remove the authenticated caller's avatar image."""
    return _to_read(user_service.remove_avatar(current_user, settings.UPLOAD_DIR))
