import uuid
from typing import Any, Dict

from fastapi import Request

from app.models import PaymentInitResult, PaymentStatus, WebhookData
from app.payments.base import PaymentGateway


class SandboxPaymentGateway(PaymentGateway):
    """
    Simple in-memory payment gateway stub for sandbox/testing.
    Mimics provider behavior without external calls.
    """

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url.rstrip("/") if base_url else "https://sandbox-pay.example.com"
        self._statuses: dict[str, PaymentStatus] = {}

    async def create_payment(self, amount_rub: int, description: str, metadata: Dict[str, Any]) -> PaymentInitResult:
        payment_id = f"sandbox_{uuid.uuid4().hex}"
        self._statuses[payment_id] = PaymentStatus.PENDING
        payment_url = f"{self.base_url}/pay/{payment_id}"
        return PaymentInitResult(payment_id=payment_id, payment_url=payment_url)

    async def verify_webhook(self, request: Request) -> WebhookData:
        payload = await request.json()
        payment_id = payload.get("payment_id", "")
        status_raw = payload.get("status", PaymentStatus.PENDING.value)
        status = PaymentStatus(status_raw) if status_raw in PaymentStatus._value2member_map_ else PaymentStatus.PENDING
        self._statuses[payment_id] = status
        return WebhookData(payment_id=payment_id, status=status, raw_payload=payload)

    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        return self._statuses.get(payment_id, PaymentStatus.PENDING)
