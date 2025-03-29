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


class Message(Document):
    """Message document for chatting"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    sender_id: str 
    receiver_id: str
    message_type: str = "text"
    content: str
    attachment_url: str=""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "message"
        indexes = [
            "sender_id",
            "created_at",
        ]

    def __repr__(self) -> str:
        """String representation of the Message object."""
        return f"Message(id={self.id}, sender_id={self.sender_id}, receiver_id={self.receiver_id}, content={self.content})"
