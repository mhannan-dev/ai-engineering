"""User management endpoints."""


from fastapi import APIRouter, status

from meeting_intelligence.api.deps import CurrentUserDep, UserServiceDep
from meeting_intelligence.schemas.user import UserCreate, UserRead

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
        full_name=user.full_name,
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
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


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
            full_name=u.full_name,
            is_active=u.is_active,
            created_at=u.created_at,
        )
        for u in users
    ]
