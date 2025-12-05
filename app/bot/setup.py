import httpx
from aiogram import Bot, Dispatcher

from app.bot.context import BotContext
from app.bot.handlers import register_handlers
from app.config import Settings
from app.dependencies import get_link_token_store
from app.core_client import CoreAPIClient


async def on_startup(ctx: BotContext) -> None:
    # Placeholder for any startup tasks (e.g., set webhook)
    ctx.integration_client.headers.update({"Content-Type": "application/json"})


async def on_shutdown(ctx: BotContext) -> None:
    await ctx.integration_client.aclose()
    await ctx.core.close()


def create_bot(settings: Settings) -> tuple[Bot, Dispatcher]:
    """Create bot and dispatcher with base handlers."""
    bot = Bot(settings.bot_token, parse_mode="HTML")
    dp = Dispatcher()

    core_client = CoreAPIClient(settings)
    integration_client = httpx.AsyncClient(base_url=settings.integration_api_base_url.rstrip("/"), timeout=10.0)
    link_tokens = get_link_token_store(settings)
    ctx = BotContext(
        settings=settings,
        core=core_client,
        integration_client=integration_client,
        link_tokens=link_tokens,
    )
    bot["ctx"] = ctx

    register_handlers(dp)
    dp.startup.register(lambda: on_startup(ctx))
    dp.shutdown.register(lambda: on_shutdown(ctx))
    return bot, dp
