from enum import Enum
from typing import Any, Dict, Union

from pydantic import BaseModel


class PaymentStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PENDING = "PENDING"
    EXPIRED = "EXPIRED"


class PaymentInitResult(BaseModel):
    payment_id: str
    payment_url: str


class WebhookData(BaseModel):
    payment_id: str
    status: PaymentStatus
    raw_payload: Union[Dict[str, Any], str]
