from functools import lru_cache

from aiogram import Bot, Dispatcher

from app.bot.setup import create_bot
from app.config import Settings, get_settings


@lru_cache(maxsize=1)
def get_bot_and_dispatcher(settings: Settings | None = None) -> tuple[Bot, Dispatcher]:
    settings = settings or get_settings()
    return create_bot(settings)
