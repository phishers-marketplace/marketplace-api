from datetime import datetime

from fastapi import APIRouter

from business.friends.models import Friendship
from business.user.models import User
from business.user.service import CurrentUser

from .models import Message
from .schemas import ListMessageResponse, MessageCreate, MessageResponse, UserContact, UserContactsListResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("", response_model=UserContactsListResponse)
async def get_contacts(current_user: CurrentUser):
    # """Get all the users with which a user has done chatting"""
    user_id = current_user.id

    # Find all friendships of the user. He can message them
    friends = await Friendship.find({"$or": [{"requester_id": user_id}, {"recipient_id": user_id}]}).to_list()

    # Extract the friend IDs (exclude user's own ID)
    friend_ids = [friend.requester_id if friend.requester_id != user_id else friend.recipient_id for friend in friends]

    # Find all users with the given friend IDs
    users = []
    for friend_id in friend_ids:
        user = await User.find_one(User.id == friend_id)
        users.append(UserContact(id=user.id, name=user.name, email=user.email, public_key=user.public_key))
    # print(users)
    return UserContactsListResponse(contacts=users, total=len(users), limit=len(users))


@router.post("/send", response_model=MessageResponse)
async def send_message(user: CurrentUser, data: MessageCreate):
    """Send a message to another user."""

    new_message = Message(
        sender_id=user.id,  # Get sender ID from authentication
        receiver_id=data.receiver_id,
        message_sender_encrypted=data.message_sender_encrypted,
        message_receiver_encrypted=data.message_receiver_encrypted,
        created_at=datetime.now(),
    )

    await new_message.save()  # Save to MongoDB
    return MessageResponse(
        id=new_message.id,
        sender_id=new_message.sender_id,
        receiver_id=new_message.receiver_id,
        message_sender_encrypted=data.message_sender_encrypted,
        message_receiver_encrypted=data.message_receiver_encrypted,
        timestamp=new_message.created_at,
    )


@router.get("/{receiver_id}", response_model=ListMessageResponse)
async def get_all_messages(user: CurrentUser, receiver_id: str):
    """Fetch chat history between two users."""

    messages = (
        await Message.find(
            {
                "$or": [
                    {"sender_id": user.id, "receiver_id": receiver_id},
                    {"sender_id": receiver_id, "receiver_id": user.id},
                ]
            }
        )
        .sort("timestamp")
        .to_list()
    )

    message_responses = [
        MessageResponse(
            id=msg.id,
            sender_id=msg.sender_id,
            receiver_id=msg.receiver_id,
            message_sender_encrypted=msg.message_sender_encrypted,
            message_receiver_encrypted=msg.message_receiver_encrypted,
            timestamp=msg.created_at,
        )
        for msg in messages
    ]
    return ListMessageResponse(messages=message_responses)
