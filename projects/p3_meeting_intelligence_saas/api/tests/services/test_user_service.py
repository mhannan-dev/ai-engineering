"""Unit tests for UserService business logic layer."""

import pytest

from meeting_intelligence.core.exceptions import NotFoundError, UnauthorizedError
from meeting_intelligence.db.session import DatabaseSession
from meeting_intelligence.schemas.user import UserCreate
from meeting_intelligence.services.user_service import UserService


def test_user_service_registration_and_auth():
    """Test user registration and successful authentication."""
    session = DatabaseSession()
    service = UserService(session)

    payload = UserCreate(email="service_test@example.com", password="SecurePassword123!", full_name="Service Tester")
    user = service.register_user(payload)

    assert user.email == "service_test@example.com"
    assert user.full_name == "Service Tester"

    # Authenticate
    authenticated = service.authenticate_user("service_test@example.com", "SecurePassword123!")
    assert authenticated.id == user.id


def test_user_service_invalid_password_raises():
    """Test authentication with wrong password raises UnauthorizedError."""
    session = DatabaseSession()
    service = UserService(session)

    payload = UserCreate(email="auth_fail@example.com", password="CorrectPassword123!")
    service.register_user(payload)

    with pytest.raises(UnauthorizedError):
        service.authenticate_user("auth_fail@example.com", "WrongPassword!")


def test_user_service_not_found_raises():
    """Test fetching nonexistent user raises NotFoundError."""
    session = DatabaseSession()
    service = UserService(session)

    with pytest.raises(NotFoundError):
        service.get_by_id("non-existent-id-000")
