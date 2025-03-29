import urllib.parse

import motor.motor_asyncio
from beanie import init_beanie

from business.friends.models import Friendship
from business.groups.models import Group, GroupMembership
from business.marketplace.items.models import Item
from business.marketplace.transactions.models import Transaction
from business.user.models import User, Message
from core.config import CONFIG

TIMEOUT = 1800


def get_mongodb_url() -> str:
    username = urllib.parse.quote_plus(CONFIG.DB.USER)
    password = urllib.parse.quote_plus(CONFIG.DB.PASSWORD)

    return f"mongodb://{username}:{password}@{CONFIG.DB.HOST}:{CONFIG.DB.PORT}/"


async def init_db():
    mongodb_url = get_mongodb_url()
    client = motor.motor_asyncio.AsyncIOMotorClient(
        mongodb_url,
        maxPoolSize=max(1, CONFIG.DB.POOL_SIZE // CONFIG.UVICORN.WORKERS),
        serverSelectionTimeoutMS=TIMEOUT,
    )
    db = client.get_database(CONFIG.DB.NAME)

    # Initialize Beanie with all document models
    await init_beanie(
        database=db,
        document_models=[
            User,
            Friendship,
            Group,
            GroupMembership,
            Item,
            Transaction,
            Message,
        ],
    )
