from fastapi import FastAPI
from uvicorn import run

from app.api import api_router
from app.api.routes import bot_webhook, health
from app.bot.loader import get_bot_and_dispatcher
from app.config import get_settings
from app.logging import setup_logging


settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    contact={"name": "Yoga Flow", "url": "https://example.com"},
)

bot, dp = get_bot_and_dispatcher(settings)


@app.on_event("startup")
async def startup_bot() -> None:
    await dp.emit_startup(bot)
    if settings.bot_webhook_url:
        await bot.set_webhook(settings.bot_webhook_url)


@app.on_event("shutdown")
async def shutdown_bot() -> None:
    if settings.bot_webhook_url:
        await bot.delete_webhook(drop_pending_updates=False)
    await dp.emit_shutdown(bot)
    await bot.session.close()


# Attach versioned API routes (placeholder for future endpoints)
app.include_router(api_router, prefix=settings.api_prefix)

# Healthcheck without prefix for external probes
app.include_router(health.router)
app.include_router(bot_webhook.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}

if __name__ == "__main__":
    run(app)
