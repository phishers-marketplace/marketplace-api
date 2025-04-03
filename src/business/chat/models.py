from datetime import UTC, datetime
from typing import List
from uuid import uuid4

from beanie import Document
from pydantic import Field


class Message(Document):
    """Message document for chatting"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    sender_id: str
    receiver_id: str
    message_type: str = "text"
    message_sender_encrypted: str
    message_receiver_encrypted: str
    attachment_url: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "message"
        indexes = [
            "sender_id",
            "created_at",
        ]

    def __repr__(self) -> str:
        """String representation of the Message object."""
        return f"Message(id={self.id}, sender_id={self.sender_id}, receiver_id={self.receiver_id}, message_sender_encrypted={self.message_sender_encrypted}, message_receiver_encrypted={self.message_receiver_encrypted})"


class ChatKey(Document):
    user_ids: List[str]  # Two users participating in the chat
    encrypted_aes_key_1: bytes  # AES key encrypted with User 1's public key
    encrypted_aes_key_2: bytes  # AES key encrypted with User 2's public key

    class Settings:
        name = "chat_keys"

    def __repr__(self) -> str:
        """String representation of the ChatKey object."""
        return f"ChatKey(user_ids={self.user_ids})"


class GroupMessage(Document):
    id: str = Field(default_factory=lambda: uuid4().hex)  # Unique identifier for the group message
    group_id: str  # Identifier for the group chat
    message: Message

    class Settings:
        name = "group_message"
        indexes = [
            "message.sender_id",
            "message.created_at",
        ]

    def __repr__(self) -> str:
        """String representation of the GroupMessage object."""
        return f"GroupMessage(id={self.id}, group={self.group_id} message={self.message})"
