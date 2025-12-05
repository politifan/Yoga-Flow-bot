from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import AliasChoices, BaseModel, Field


class SubscriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"


class User(BaseModel):
    id: str
    email: Optional[str] = None
    phone: Optional[str] = None
    telegram_user_id: Optional[int] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None
    avatar_letter: Optional[str] = None
    default_plan: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"extra": "ignore"}


class Tariff(BaseModel):
    id: str
    name: str
    price_rub: Optional[int] = Field(default=None, description="Цена в копейках")
    price_usd: Optional[int] = None
    tagline: Optional[str] = None
    features: Optional[List[str]] = None

    model_config = {"extra": "ignore"}


class Transaction(BaseModel):
    id: str
    user_id: str
    tariff_id: str
    amount: int
    currency: str
    status: TransactionStatus
    source: Optional[str] = None
    payment_provider: Optional[str] = None
    provider_payment_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"extra": "ignore"}


class CreateTransactionRequest(BaseModel):
    user_id: str
    tariff_id: str
    amount: int
    currency: str = "RUB"
    source: str = "site"
    payment_provider: str = "sandbox"
    metadata: dict[str, Any] = Field(default_factory=dict)


class PatchTransactionRequest(BaseModel):
    status: TransactionStatus
    provider_payment_id: Optional[str] = None
    provider_payload: Optional[dict[str, Any]] = None


class Subscription(BaseModel):
    id: str
    user_id: str
    tariff_id: str
    status: SubscriptionStatus
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = Field(
        default=None, validation_alias=AliasChoices("expires_at", "ends_at")
    )
    created_at: Optional[datetime] = None

    model_config = {"extra": "ignore", "populate_by_name": True}


class CreateSubscriptionRequest(BaseModel):
    user_id: str
    tariff_id: str
    transaction_id: str
    expires_at: datetime


class Course(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    url: Optional[str] = None

    model_config = {"extra": "ignore"}


class Call(BaseModel):
    id: str
    title: str
    start_at: datetime
    discord_link: Optional[str] = None
    description: Optional[str] = None

    model_config = {"extra": "ignore"}
