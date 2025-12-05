from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Yoga Flow Integrator"
    environment: str = Field(default="local", description="Deployment environment tag")
    log_level: str = Field(default="INFO", description="Logging level")
    api_prefix: str = "/api"

    core_api_base_url: str = Field(default="https://core.example.com", description="Base URL for Core API")
    service_token: str = Field(default="changeme-service-token", description="Service token for Core API")

    bot_token: str = Field(default="changeme-telegram-bot-token", description="Telegram bot token")
    bot_username: Optional[str] = Field(default=None, description="Telegram bot username (for deeplinks)")
    bot_webhook_url: Optional[str] = Field(default=None, description="Webhook URL for Telegram updates")

    payment_provider: str = Field(default="sandbox", description="Payment provider identifier")
    payment_base_url: Optional[str] = Field(default=None, description="Base URL for payment provider")
    payment_secret: Optional[str] = Field(default=None, description="Secret for webhook verification")
    payment_public_key: Optional[str] = Field(default=None, description="Public key for provider (if required)")

    link_token_ttl_seconds: int = Field(default=900, description="TTL for Telegram link tokens in seconds")

    integration_api_base_url: str = Field(
        default="http://localhost:8000/api/v1", description="Base URL for this integration API (for bot calls)"
    )

    http_max_retries: int = Field(default=2, description="Retries for outgoing HTTP calls to Core API")
    http_retry_backoff: float = Field(default=0.5, description="Backoff seconds between retries")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
