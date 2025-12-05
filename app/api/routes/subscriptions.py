from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.core_client import (
    CoreAPIClient,
    CoreAPIError,
    CreateTransactionRequest,
    PatchTransactionRequest,
    Tariff,
    TransactionStatus,
)
from app.dependencies import get_core_client, get_gateway
from app.payments import PaymentGateway


class CreatePaymentSessionRequest(BaseModel):
    user_id: str
    tariff_id: str
    source: str = Field(default="site", description="site|bot")


class CreatePaymentSessionResponse(BaseModel):
    transaction_id: str
    payment_url: str
    provider_payment_id: str
    amount: int
    currency: str = "RUB"


router = APIRouter()


def _pick_tariff(tariffs: list[Tariff], tariff_id: str) -> Tariff:
    for t in tariffs:
        if t.id == tariff_id:
            return t
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff not found")


def _tariff_amount_rub(tariff: Tariff) -> int:
    if tariff.price_rub is not None:
        return int(tariff.price_rub)
    if tariff.price_usd is not None:
        return int(tariff.price_usd * 100)
    raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Tariff has no price")


@router.post("/create_payment_session", response_model=CreatePaymentSessionResponse)
async def create_payment_session(
    payload: CreatePaymentSessionRequest,
    core: CoreAPIClient = Depends(get_core_client),
    gateway: PaymentGateway = Depends(get_gateway),
    settings: Settings = Depends(get_settings),
) -> CreatePaymentSessionResponse:
    try:
        tariffs = await core.get_tariffs()
        tariff = _pick_tariff(tariffs, payload.tariff_id)
        amount_rub = _tariff_amount_rub(tariff)

        tx_req = CreateTransactionRequest(
            user_id=payload.user_id,
            tariff_id=payload.tariff_id,
            amount=amount_rub,
            currency="RUB",
            source=payload.source,
            payment_provider=settings.payment_provider,
            metadata={"source": payload.source},
        )
        transaction = await core.create_transaction(tx_req)

        description = f"Yoga Flow {tariff.name}"
        payment = await gateway.create_payment(
            amount_rub=amount_rub,
            description=description,
            metadata={
                "user_id": payload.user_id,
                "tariff_id": payload.tariff_id,
                "transaction_id": transaction.id,
                "source": payload.source,
            },
        )

        patch_req = PatchTransactionRequest(
            status=TransactionStatus.PENDING,
            provider_payment_id=payment.payment_id,
            provider_payload={"create_payment": "ok"},
        )
        await core.patch_transaction(transaction.id, patch_req)

        return CreatePaymentSessionResponse(
            transaction_id=transaction.id,
            payment_url=payment.payment_url,
            provider_payment_id=payment.payment_id,
            amount=amount_rub,
        )
    except CoreAPIError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"code": err.code, "message": str(err), "details": err.details},
        ) from err
