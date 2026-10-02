"""User management endpoints."""

from fastapi import APIRouter, File, UploadFile, status

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
async def create_user(payload: UserCreate, user_service: UserServiceDep) -> UserRead:
    """Register a new user account."""
    user = user_service.register_user(payload)
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


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    description="Retrieve the profile of the authenticated caller.",
)
async def get_me(current_user: CurrentUserDep) -> UserRead:
    """Return authenticated caller's profile."""
    return UserRead(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        avatar=current_user.avatar,
        subscription_tier=current_user.subscription_tier,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current user",
    description="Update the profile of the authenticated caller.",
)
async def update_me(
    payload: UserUpdate, current_user: CurrentUserDep, user_service: UserServiceDep
) -> UserRead:
    """Update authenticated caller's profile."""
    user = user_service.update_user(
        user_id=current_user.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )
    return _to_read(user)


@router.get(
    "/",
    response_model=list[UserRead],
    summary="List all users",
    description="Retrieve list of all registered accounts (requires authentication).",
)
async def list_users(_: CurrentUserDep, user_service: UserServiceDep) -> list[UserRead]:
    """List registered users."""
    users = user_service.list_users()
    return [
        UserRead(
            id=u.id,
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            avatar=u.avatar,
            subscription_tier=u.subscription_tier,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]


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
    user = user_service.update_avatar(
        current_user, content, settings.UPLOAD_DIR, settings.AVATAR_MAX_BYTES
    )
    return _to_read(user)


@router.delete(
    "/me/avatar",
    response_model=UserRead,
    summary="Remove avatar",
    description="Delete the caller's avatar image.",
)
async def delete_avatar(
    current_user: CurrentUserDep, user_service: UserServiceDep, settings: SettingsDep
) -> UserRead:
    """Remove the authenticated caller's avatar image."""
    return _to_read(user_service.remove_avatar(current_user, settings.UPLOAD_DIR))
