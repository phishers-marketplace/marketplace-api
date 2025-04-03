from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from beanie import Document
from pydantic import Field


class FriendshipStatus(str, Enum):
    """Status of a friendship between users"""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class Friendship(Document):
    """Friendship document for MongoDB storage"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    requester_id: str  # User who initiated the friendship
    recipient_id: str  # User who received the request
    status: FriendshipStatus = FriendshipStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "friendships"
        indexes = [
            "requester_id",
            "recipient_id",
            "status",
            "created_at",
        ]

    def __repr__(self) -> str:
        """String representation of the Friendship object."""
        return f"Friendship(id={self.id}, requester_id={self.requester_id}, recipient_id={self.recipient_id}, status={self.status})"
