import asyncio

from aiogram import Bot

from app.bot.setup import create_bot
from app.config import get_settings


async def main() -> None:
    settings = get_settings()
    bot, dp = create_bot(settings)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
