from datetime import UTC, datetime
from enum import Enum
from uuid import uuid4

from beanie import Document
from pydantic import Field


class TransactionStatus(str, Enum):
    """Status of a transaction in the marketplace"""

    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    """Payment methods for transactions"""

    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    OTHER = "other"


class Transaction(Document):
    """Transaction document for MongoDB storage"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    item_id: str
    buyer_id: str
    seller_id: str
    price: float
    status: TransactionStatus = TransactionStatus.PENDING
    payment_method: PaymentMethod | None = None
    payment_id: str | None = None  # ID from payment processor if applicable
    shipping_address: str | None = None
    tracking_number: str | None = None
    notes: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None

    class Settings:
        name = "marketplace_transactions"
        indexes = [
            "item_id",
            "buyer_id",
            "seller_id",
            "status",
            "created_at",
        ]

    def __repr__(self) -> str:
        """String representation of the Transaction object."""
        return f"Transaction(id={self.id}, item_id={self.item_id}, buyer_id={self.buyer_id}, seller_id={self.seller_id}, status={self.status})"
