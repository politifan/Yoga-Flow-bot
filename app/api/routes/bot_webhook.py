from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.dependencies import get_bot_instance, get_dispatcher

router = APIRouter()


@router.post("/bot/webhook")
async def bot_webhook(
    request: Request,
    bot: Bot = Depends(get_bot_instance),
    dp: Dispatcher = Depends(get_dispatcher),
) -> dict:
    try:
        data = await request.json()
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON")

    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"status": "ok"}
