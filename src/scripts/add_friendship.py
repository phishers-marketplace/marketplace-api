#!/usr/bin/env python3
"""
Script to add an accepted friendship between two users.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Add the project root to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from business.friends.models import Friendship, FriendshipStatus
from core.db import init_db


async def add_friendship(user1_id: str, user2_id: str) -> Optional[Friendship]:
    """
    Add an accepted friendship between two users.

    Args:
        user1_id: ID of the first user
        user2_id: ID of the second user

    Returns:
        The created Friendship object if successful, None otherwise
    """
    # Check if friendship already exists
    existing_friendship = await Friendship.find_one(
        {
            "$or": [
                {"requester_id": user1_id, "recipient_id": user2_id},
                {"requester_id": user2_id, "recipient_id": user1_id},
            ]
        }
    )

    if existing_friendship:
        print(f"Friendship already exists between users {user1_id} and {user2_id}")
        return None

    # Create new friendship
    friendship = Friendship(requester_id=user1_id, recipient_id=user2_id, status=FriendshipStatus.ACCEPTED)

    await friendship.save()
    print(f"Successfully created friendship between users {user1_id} and {user2_id}")
    return friendship


async def main():
    if len(sys.argv) != 3:
        print("Usage: python add_friendship.py <user1_id> <user2_id>")
        sys.exit(1)

    user1_id = sys.argv[1]
    user2_id = sys.argv[2]

    # Initialize database connection
    await init_db()

    # Add friendship
    friendship = await add_friendship(user1_id, user2_id)
    if friendship:
        print(f"Friendship created with ID: {friendship.id}")


if __name__ == "__main__":
    asyncio.run(main())
