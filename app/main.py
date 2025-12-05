from fastapi import FastAPI

from app.api import api_router
from app.api.routes import health
from app.config import get_settings
from app.logging import setup_logging


settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    contact={"name": "Yoga Flow", "url": "https://example.com"},
)

# Attach versioned API routes (placeholder for future endpoints)
app.include_router(api_router, prefix=settings.api_prefix)

# Healthcheck without prefix for external probes
app.include_router(health.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
