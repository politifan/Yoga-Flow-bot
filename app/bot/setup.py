from aiogram import Bot, Dispatcher

from app.config import Settings
from app.bot.handlers import register_handlers


def create_bot(settings: Settings) -> tuple[Bot, Dispatcher]:
    """Create bot and dispatcher with base handlers."""
    bot = Bot(settings.bot_token, parse_mode="HTML")
    dp = Dispatcher()
    register_handlers(dp)
    return bot, dp
