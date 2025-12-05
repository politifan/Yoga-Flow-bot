from abc import ABC, abstractmethod
from typing import Any, Dict

from fastapi import Request

from app.models import PaymentInitResult, PaymentStatus, WebhookData


class PaymentGateway(ABC):
    @abstractmethod
    async def create_payment(self, amount_rub: int, description: str, metadata: Dict[str, Any]) -> PaymentInitResult:
        """
        amount_rub – сумма в копейках.
        Should return provider payment_id and payment_url for the customer.
        """

    @abstractmethod
    async def verify_webhook(self, request: Request) -> WebhookData:
        """
        Verify webhook signature and parse payload.
        Must return payment_id, status, and raw payload for logging.
        """

    @abstractmethod
    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """
        Retrieve current status from provider (idempotent check).
        """
