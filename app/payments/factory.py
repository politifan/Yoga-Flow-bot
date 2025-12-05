from app.config import Settings
from app.payments import SandboxPaymentGateway
from app.payments.base import PaymentGateway


def get_payment_gateway(settings: Settings) -> PaymentGateway:
    """
    Simple factory for payment gateways.
    Extend with additional providers when needed.
    """
    provider = settings.payment_provider.lower()
    if provider == "sandbox":
        return SandboxPaymentGateway(base_url=settings.payment_base_url, secret=settings.payment_secret)
    raise ValueError(f"Unsupported payment provider: {settings.payment_provider}")
