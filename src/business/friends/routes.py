from fastapi import APIRouter, Query
from datetime import datetime
from business.friends.models import Friendship
from business.friends.schemas import AddFriendResponse
from business.user.schemas import UserListResponse
from business.user.models import User
from business.user.service import CurrentUser

DEFAULT_PAGE_SIZE = 10

router = APIRouter(prefix="/friends", tags=["user"])

@router.post("/add_friend/{friend_id}", response_model=AddFriendResponse)
async def add_friend(user: CurrentUser, friend_id: str):
    # add friend to the user in the friendship document 
    new_friendship = Friendship(
        requester_id=user.id,
        recipient_id=friend_id,
        status='accepted',
        created_at=datetime.now(),
    )
    await new_friendship.save()  # Save to MongoDB
    return AddFriendResponse(
        id=new_friendship.id,
        requester_id=new_friendship.requester_id,
        recipient_id=new_friendship.recipient_id,
        status=new_friendship.status,
        created_at=new_friendship.created_at,
    )


@router.get("/add_friend/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=100, description="Items per page"),
    search: str = Query(None, description="Search by name or email"),
):
    """List all users """
    
   
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

    # Get total count for pagination
    total = await User.find(query).count()

    # Get users with pagination
    users = await User.find(query).sort(-User.created_at).skip(skip).limit(limit).to_list()
    return UserListResponse(users=users, total=total, page=page, limit=limit)