from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


class MessageCreate(BaseModel):
    """Schema for creating a new message"""

    receiver_id: str
    message_sender_encrypted: str
    message_receiver_encrypted: str


class MessageResponse(BaseModel):
    """Schema for message response"""

    id: str
    sender_id: str
    receiver_id: str
    message_sender_encrypted: str
    message_receiver_encrypted: str
    timestamp: datetime


class ListMessageResponse(BaseModel):
    """Schema for list of messages response"""

    messages: List[MessageResponse]


class UserContact(BaseModel):
    """Schema for user contact"""

    id: str
    name: str
    email: EmailStr
    public_key: str


class UserContactsListResponse(BaseModel):
    """Schema for list of user contacts response"""

    contacts: List[UserContact]
    total: int
    limit: int
