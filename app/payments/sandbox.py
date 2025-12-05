import hashlib
import hmac
import json
import logging
import uuid
from typing import Any, Dict, Optional

from fastapi import Request

from app.models import PaymentInitResult, PaymentStatus, WebhookData
from app.payments.base import PaymentGateway

logger = logging.getLogger(__name__)


class SandboxPaymentGateway(PaymentGateway):
    """
    Simple in-memory payment gateway stub for sandbox/testing.
    Mimics provider behavior without external calls.
    """

    def __init__(self, base_url: str | None = None, secret: Optional[str] = None):
        self.base_url = base_url.rstrip("/") if base_url else "https://sandbox-pay.example.com"
        self.secret = secret
        self._statuses: dict[str, PaymentStatus] = {}
        self._webhook_payloads: dict[str, dict[str, Any]] = {}

    async def create_payment(self, amount_rub: int, description: str, metadata: Dict[str, Any]) -> PaymentInitResult:
        payment_id = f"sandbox_{uuid.uuid4().hex}"
        self._statuses[payment_id] = PaymentStatus.PENDING
        payment_url = f"{self.base_url}/pay/{payment_id}"
        logger.info("Sandbox payment created %s amount=%s", payment_id, amount_rub)
        return PaymentInitResult(payment_id=payment_id, payment_url=payment_url)

    async def verify_webhook(self, request: Request) -> WebhookData:
        raw_body = await request.body()
        signature = request.headers.get("X-Signature")
        if self.secret and signature:
            expected = hmac.new(self.secret.encode(), raw_body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, signature):
                raise ValueError("Invalid webhook signature")

        payload = json.loads(raw_body or "{}")
        payment_id = payload.get("payment_id", "")
        status_raw = payload.get("status", PaymentStatus.PENDING.value)
        status = PaymentStatus(status_raw) if status_raw in PaymentStatus._value2member_map_ else PaymentStatus.PENDING
        self._statuses[payment_id] = status
        self._webhook_payloads[payment_id] = payload
        logger.info("Sandbox webhook received %s status=%s", payment_id, status)
        return WebhookData(payment_id=payment_id, status=status, raw_payload=payload)

    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        return self._statuses.get(payment_id, PaymentStatus.PENDING)

    def get_raw_payload(self, payment_id: str) -> dict[str, Any] | None:
        return self._webhook_payloads.get(payment_id)
