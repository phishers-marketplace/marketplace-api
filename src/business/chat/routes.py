from datetime import datetime

from fastapi import APIRouter

from business.user.models import User
from business.user.service import CurrentUser

from .models import Message
from .schemas import ListMessageResponse, MessageCreate, MessageResponse, UserContact, UserContactsListResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("", response_model=UserContactsListResponse)
async def get_contacts(current_user: CurrentUser):
    """Get all the users with which a user has done chatting"""
    user_id = current_user.id

    # Distinct users the given user has sent messages to
    sent_to = await Message.distinct("receiver_id", {"sender_id": user_id})
    received_from = await Message.distinct("sender_id", {"receiver_id": user_id})

    # Combine and remove duplicates
    contacts = list(set(sent_to + received_from))

    # Find all users with user id given in the list
    users = []
    for contact in contacts:
        user = await User.find_one(User.id == contact, User.is_suspended == False)
        if user:  # Only add if user exists
            users.append(user)

    return UserContactsListResponse(
        contacts=[UserContact(id=user.id, name=user.name, email=user.email) for user in users]
    )


@router.post("/send", response_model=MessageResponse)
async def send_message(current_user: CurrentUser, data: MessageCreate):
    """Send a message to another user."""
    new_message = Message(
        sender_id=current_user.id,
        receiver_id=data.receiver_id,
        content=data.message,
        created_at=datetime.now(),
    )

    await new_message.save()
    return MessageResponse(
        id=new_message.id,
        sender_id=new_message.sender_id,
        receiver_id=new_message.receiver_id,
        message=new_message.content,
        timestamp=new_message.created_at,
    )


@router.get("/{receiver_id}", response_model=ListMessageResponse)
async def get_all_messages(current_user: CurrentUser, receiver_id: str):
    """Fetch chat history between two users."""
    messages = (
        await Message.find(
            {
                "$or": [
                    {"sender_id": current_user.id, "receiver_id": receiver_id},
                    {"sender_id": receiver_id, "receiver_id": current_user.id},
                ]
            }
        )
        .sort("created_at")
        .to_list()
    )

    message_responses = [
        MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            message=msg.content,
            timestamp=msg.created_at,
        )
        for msg in messages
    ]

    return ListMessageResponse(messages=message_responses)
