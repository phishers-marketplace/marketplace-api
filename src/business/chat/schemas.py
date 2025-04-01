from datetime import datetime
from typing import List

from pydantic import BaseModel, EmailStr


class MessageCreate(BaseModel):
    """Schema for creating a new message"""

    receiver_id: str
    message: str


class MessageResponse(BaseModel):
    """Schema for message response"""

    id: str
    sender_id: str
    receiver_id: str
    message: str
    timestamp: datetime


class ListMessageResponse(BaseModel):
    """Schema for list of messages response"""

    messages: List[MessageResponse]


class UserContact(BaseModel):
    """Schema for user contact"""

    id: str
    name: str
    email: EmailStr


class UserContactsListResponse(BaseModel):
    """Schema for list of user contacts response"""

    contacts: List[UserContact]
