"""User domain entity."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class User:
    """User domain entity for authentication and ownership."""

    email: str
    hashed_password: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    first_name: str = ""
    last_name: str | None = None
    # Read-only: URL of the user's avatar, resolved from the uploads table
    avatar: str | None = None
    subscription_tier: str = "free"
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
