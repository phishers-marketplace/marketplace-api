from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from beanie import Document
from pydantic import Field


class MemberRole(str, Enum):
    """Role of a member in a group"""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class Group(Document):
    """Group document for MongoDB storage"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str
    description: str = ""
    created_by: str  # User ID of the creator
    # is_public: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    # updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "groups"
        indexes = [
            "name",
            "created_by",
            "created_at",
        ]

    def __repr__(self) -> str:
        """String representation of the Group object."""
        return f"Group(id={self.id}, name={self.name}, created_by={self.created_by})"


class GroupMembership(Document):
    """Group membership document for MongoDB storage"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    group_id: str
    user_id: str
    role: MemberRole
    joined_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    invited_by: str | None = None  # User ID of the person who invited this member

    class Settings:
        name = "group_memberships"
        indexes = [
            "group_id",
            "user_id",
            "role",
            "joined_at",
        ]

    def __repr__(self) -> str:
        """String representation of the GroupMembership object."""
        return f"GroupMembership(id={self.id}, group_id={self.group_id}, user_id={self.user_id}, role={self.role})"

