import logging

from aiogram import Bot
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core_client import CoreAPIClient, CoreAPIError
from app.dependencies import get_bot_instance, get_core_client
from app.services.receipts import ReceiptService

logger = logging.getLogger(__name__)


class ReceiptResponse(BaseModel):
    transaction_id: str
    receipt_text: str
    delivered_to_telegram: bool = False


router = APIRouter()


@router.post("/transactions/{transaction_id}/send_receipt", response_model=ReceiptResponse)
async def send_receipt(
    transaction_id: str,
    core: CoreAPIClient = Depends(get_core_client),
    bot: Bot = Depends(get_bot_instance),
) -> ReceiptResponse:
    try:
        service = ReceiptService(core)
        text, user = await service.build_text_receipt(transaction_id)

        delivered = False
        if user.telegram_user_id:
            try:
                await bot.send_message(chat_id=user.telegram_user_id, text=text)
                delivered = True
            except Exception as send_err:  # noqa: BLE001
                logger.warning("Failed to send receipt to Telegram: %s", send_err)

        return ReceiptResponse(transaction_id=transaction_id, receipt_text=text, delivered_to_telegram=delivered)
    except CoreAPIError as err:
        raise HTTPException(
            status_code=err.status_code,
            detail={"code": err.code, "message": str(err), "details": err.details},
        ) from err
