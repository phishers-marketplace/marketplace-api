from datetime import timedelta
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from core.config import CONFIG

from business.groups.models import GroupMembership, Group
from business.friends.models import Friendship
from business.groups.schemas import GroupsListResponse, GroupSchema
from .models import User, Message
from .schemas import Token, UserCreate, UserListResponse, UserLogin, UserSchema, UserSuspend, UserUpdateAdmin, UserContactsListResponse, MessageCreate, MessageResponse, ListMessageResponse
from .service import AdminUser, CurrentUser, authenticate_user, create_access_token, get_password_hash, generate_rsa_keys, encrypt_private_key, decrypt_private_key
from cryptography.hazmat.primitives import serialization

router = APIRouter(prefix="/user", tags=["user"])
DEFAULT_PAGE_SIZE = 10

@router.get("/me", response_model=UserSchema)
async def get_me(current_user: CurrentUser):
    """Get information about the currently authenticated user."""
    return current_user


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate) -> UserSchema:
    """Register a new user with email and password."""
    global password
    password='reg'
    # Check if user with this email already exists
    existing_user = await User.find_one(User.email == user_data.email.lower())
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User with this email already exists")

    # Create new user with hashed password
    password_hash = get_password_hash(user_data.password)
   
    new_user = User(
        name=user_data.name,
        email=user_data.email.lower(),
        password_hash=password_hash,
        public_key=user_data.public_key, 
        encrypted_private_key=user_data.encrypted_private_key,
        salt=user_data.salt,
        iv=user_data.iv,
    )
    print(new_user)
    
    await new_user.insert()
    return new_user


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: UserLogin) -> Token:
    """OAuth2 compatible token login, get an access token for future requests."""
    user = await authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(days=CONFIG.SECURITY.ACCESS_TOKEN_EXPIRE_DAYS)
    access_token = create_access_token(
        data={"sub": user.email, "name": user.name, "is_admin": user.is_admin}, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


# Admin routes for user management
@router.get("/admin/users", response_model=UserListResponse, tags=["admin"])
async def list_users(
    admin_user: AdminUser,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Items per page"),
    search: str = Query(None, description="Search by name or email"),
    show_suspended: bool = Query(False, description="Show suspended users only"),
):
    """List all users (admin only)."""
    print('here2')
    print(admin_user.id)
    skip = (page - 1) * limit

    # Build the query
    query = {}
    if search:
        # Search in name or email
        query = {
            "$or": [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
            ]
        }

    if show_suspended:
        query["is_suspended"] = True

    # Get total count for pagination
    total = await User.find(query).count()

    # Get users with pagination
    users = await User.find(query).sort(-User.created_at).skip(skip).limit(limit).to_list()

    return UserListResponse(users=users, total=total, page=page, limit=limit)


@router.get("/admin/users/{user_id}", response_model=UserSchema, tags=["admin"])
async def get_user(admin_user: AdminUser, user_id: str = Path(..., description="User ID")):
    """Get user details by ID (admin only)."""
    user = await User.find_one(User.id == user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


@router.patch("/admin/users/{user_id}", response_model=UserSchema, tags=["admin"])
async def update_user(
    admin_user: AdminUser,
    user_data: UserUpdateAdmin,
    user_id: str = Path(..., description="User ID"),
):
    """Update user profile (admin only)."""
    user = await User.find_one(User.id == user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Apply updates
    update_data = user_data.model_dump(exclude_unset=True)

    # If email is being updated, check for conflicts
    if "email" in update_data and update_data["email"] != user.email:
        existing = await User.find_one(User.email == update_data["email"].lower())
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already in use by another account"
            )
        update_data["email"] = update_data["email"].lower()

    # Update user
    for field, value in update_data.items():
        setattr(user, field, value)

    await user.save()
    return user


@router.post("/admin/users/{user_id}/suspend", response_model=UserSchema, tags=["admin"])
async def suspend_user(
    admin_user: AdminUser,
    suspension_data: UserSuspend,
    user_id: str = Path(..., description="User ID"),
):
    """Suspend a user account (admin only)."""
    user = await User.find_one(User.id == user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot suspend an admin account")

    user.is_suspended = True
    user.suspension_reason = suspension_data.suspension_reason

    await user.save()
    return user


@router.post("/admin/users/{user_id}/unsuspend", response_model=UserSchema, tags=["admin"])
async def unsuspend_user(
    admin_user: AdminUser,
    user_id: str = Path(..., description="User ID"),
):
    """Reactivate a suspended user account (admin only)."""
    user = await User.find_one(User.id == user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_suspended = False
    user.suspension_reason = None

    await user.save()
    return user


@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["admin"])
async def delete_user(
    admin_user: AdminUser,
    user_id: str = Path(..., description="User ID"),
):
    """Delete a user account (admin only)."""
    user = await User.find_one(User.id == user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete an admin account")

    await user.delete()
    return None



@router.get("/chat", response_model=UserContactsListResponse)
async def get_contacts(current_user: CurrentUser):
    # """Get all the users with which a user has done chatting"""
        user_id = current_user.id
        
        # Find all friendships of the user. He can message them 
        friends = await Friendship.find(
        {
            "$or": [
                {"requester_id": user_id},
                {"recipient_id": user_id}
            ]
        }
        ).to_list()

        # Extract the friend IDs (exclude user's own ID)
        friend_ids = [
            friend.requester_id if friend.requester_id != user_id else friend.recipient_id
            for friend in friends
        ]

        # Find all users with the given friend IDs
        users=[]
        for friend_id in friend_ids:
            user = await User.find_one(User.id == friend_id)
            users.append(user)
        # print(users)
        return UserContactsListResponse(contacts=users, total=len(users), limit=len(users))
        
    
@router.get("/groups", response_model=GroupsListResponse)
async def get_groups(current_user: CurrentUser):
     # get all group_id objects where the user is a member
        groups = await GroupMembership.distinct("user_id", {"user_id": current_user.id})
        print('groups:',groups)
        groups_list=[]
        
        #find all group objects where user is a member
        for group in groups: 
            groups_list.append(Group.find_one(Group.id == group.id))
        return GroupsListResponse(groups_list=groups_list)
    

@router.post("/chat/send", response_model=MessageResponse)
async def send_message(user: CurrentUser,data: MessageCreate):
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
        
        
@router.get("/chat/{receiver_id}", response_model=ListMessageResponse)
async def get_all_messages(user:CurrentUser,receiver_id: str):
    """Fetch chat history between two users."""
   
    messages = await Message.find(
        {
            "$or": [
                {"sender_id": user.id, "receiver_id": receiver_id},
                {"sender_id": receiver_id, "receiver_id": user.id},
            ]
        }
    ).sort("timestamp").to_list()

   
    message_responses = [MessageResponse(id=msg.id,sender_id=msg.sender_id,receiver_id=msg.receiver_id,message_sender_encrypted=msg.message_sender_encrypted,message_receiver_encrypted=msg.message_receiver_encrypted,timestamp=msg.created_at) for msg in messages]
    return ListMessageResponse(messages=message_responses)