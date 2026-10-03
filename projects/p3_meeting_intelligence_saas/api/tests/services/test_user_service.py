"""Unit tests for UserService business logic layer."""

import pytest

from meeting_intelligence.core.exceptions import NotFoundError, UnauthorizedError
from meeting_intelligence.schemas.user import UserCreate
from meeting_intelligence.services.user_service import UserService


def test_user_service_registration_and_auth(db_session):
    """Test user registration and successful authentication."""
    service = UserService(db_session)

    payload = UserCreate(
        email="service_test@example.com", password="SecurePassword123!", first_name="Service", last_name="Tester"
    )
    user = service.register_user(payload)

    assert user.email == "service_test@example.com"
    assert (user.first_name, user.last_name) == ("Service", "Tester")
    assert user.hashed_password != "SecurePassword123!"

    authenticated = service.authenticate_user("service_test@example.com", "SecurePassword123!")
    assert authenticated.id == user.id


def test_user_service_invalid_password_raises(db_session):
    """Test authentication with wrong password raises UnauthorizedError."""
    service = UserService(db_session)
    service.register_user(UserCreate(email="auth_fail@example.com", password="CorrectPassword123!", first_name="A"))

    with pytest.raises(UnauthorizedError):
        service.authenticate_user("auth_fail@example.com", "WrongPassword!")


def test_user_service_not_found_raises(db_session):
    """Test fetching nonexistent user raises NotFoundError."""
    with pytest.raises(NotFoundError):
        UserService(db_session).get_by_id("non-existent-id-000")
