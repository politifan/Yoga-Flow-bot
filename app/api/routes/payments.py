from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core_client import CoreAPIClient, CoreAPIError, CreateSubscriptionRequest, PatchTransactionRequest, TransactionStatus
from app.dependencies import get_core_client, get_gateway
from app.models import PaymentStatus
from app.payments import PaymentGateway

router = APIRouter()

PAYMENT_TO_TRANSACTION = {
    PaymentStatus.SUCCESS: TransactionStatus.SUCCESS,
    PaymentStatus.FAILED: TransactionStatus.FAILED,
    PaymentStatus.EXPIRED: TransactionStatus.EXPIRED,
    PaymentStatus.PENDING: TransactionStatus.PENDING,
}


@router.post("/webhook")
async def payment_webhook(
    request: Request,
    gateway: PaymentGateway = Depends(get_gateway),
    core: CoreAPIClient = Depends(get_core_client),
) -> Dict[str, Any]:
    try:
        webhook_data = await gateway.verify_webhook(request)
        transaction = await core.get_transaction_by_provider_id(webhook_data.payment_id)

        if not transaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")

        new_status = PAYMENT_TO_TRANSACTION.get(webhook_data.status, TransactionStatus.PENDING)

        if transaction.status == TransactionStatus.SUCCESS and new_status == TransactionStatus.SUCCESS:
            return {"status": "ok", "transaction_id": transaction.id, "message": "already processed"}
        if transaction.status == TransactionStatus.FAILED and new_status == TransactionStatus.FAILED:
            return {"status": "ok", "transaction_id": transaction.id, "message": "already failed"}

        provider_payload = (
            webhook_data.raw_payload if isinstance(webhook_data.raw_payload, dict) else {"raw": webhook_data.raw_payload}
        )

        patch_req = PatchTransactionRequest(
            status=new_status,
            provider_payment_id=webhook_data.payment_id,
            provider_payload=provider_payload,
        )
        updated_tx = await core.patch_transaction(transaction.id, patch_req)

        response: Dict[str, Any] = {
            "status": "ok",
            "transaction_id": updated_tx.id,
            "new_status": updated_tx.status,
        }

        if webhook_data.status == PaymentStatus.SUCCESS:
            # Default to 30 days if tariff duration is not defined in Core API
            duration_days = 30
            expires_at = datetime.now(timezone.utc) + timedelta(days=duration_days)
            sub_req = CreateSubscriptionRequest(
                user_id=updated_tx.user_id,
                tariff_id=updated_tx.tariff_id,
                transaction_id=updated_tx.id,
                expires_at=expires_at,
            )
            subscription = await core.create_subscription(sub_req)
            response["subscription_id"] = subscription.id
            response["expires_at"] = subscription.expires_at

        return response
    except CoreAPIError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"code": err.code, "message": str(err), "details": err.details},
        ) from err
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
