from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from beanie import Document
from pydantic import Field


class ItemStatus(str, Enum):
    """Status of an item in the marketplace"""

    DRAFT = "draft"
    ACTIVE = "active"
    SOLD = "sold"
    REMOVED = "removed"


class ItemCategory(str, Enum):
    """Categories for marketplace items"""

    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    HOME = "home"
    BOOKS = "books"
    SPORTS = "sports"
    TOYS = "toys"
    VEHICLES = "vehicles"
    OTHER = "other"


class Item(Document):
    """Item document for MongoDB storage"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    title: str
    description: str
    price: float
    seller_id: str  # User ID of the seller
    category: ItemCategory = ItemCategory.OTHER
    status: ItemStatus = ItemStatus.DRAFT
    location: str | None = None
    images: list[str] = []  # List of image URLs
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "marketplace_items"
        indexes = [
            "seller_id",
            "category",
            "status",
            "price",
            "created_at",
        ]

    def __repr__(self) -> str:
        """String representation of the Item object."""
        return f"Item(id={self.id}, title={self.title}, price={self.price}, status={self.status})"
