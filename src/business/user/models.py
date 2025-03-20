from datetime import UTC, datetime
from uuid import uuid4

from beanie import Document
from pydantic import EmailStr, Field


class User(Document):
    """User document for MongoDB storage"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    email: EmailStr
    password_hash: str
    is_admin: bool = False
    is_suspended: bool = False
    suspension_reason: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "users"
        indexes = [
            "email",
            "created_at",
        ]

    def __repr__(self) -> str:
        """String representation of the User object."""
        return f"User(id={self.id}, name={self.name}, email={self.email})"
