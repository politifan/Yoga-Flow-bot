from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends

from app.config import Settings, get_settings
from app.core_client import CoreAPIClient
from app.payments import PaymentGateway, get_payment_gateway
from app.services.link_tokens import LinkTokenStore
from aiogram import Bot, Dispatcher
from app.bot.loader import get_bot_and_dispatcher


@lru_cache(maxsize=1)
def _get_gateway_cached(settings: Settings) -> PaymentGateway:
    return get_payment_gateway(settings)


async def get_core_client(settings: Settings = Depends(get_settings)) -> AsyncGenerator[CoreAPIClient, None]:
    client = CoreAPIClient(settings)
    try:
        yield client
    finally:
        await client.close()


def get_gateway(settings: Settings = Depends(get_settings)) -> PaymentGateway:
    return _get_gateway_cached(settings)


@lru_cache(maxsize=1)
def _get_link_token_store(ttl_seconds: int) -> LinkTokenStore:
    return LinkTokenStore(ttl_seconds=ttl_seconds)


def get_link_token_store(settings: Settings = Depends(get_settings)) -> LinkTokenStore:
    return _get_link_token_store(settings.link_token_ttl_seconds)


def get_bot_instance(settings: Settings = Depends(get_settings)) -> Bot:
    bot, _ = get_bot_and_dispatcher(settings)
    return bot


def get_dispatcher(settings: Settings = Depends(get_settings)) -> Dispatcher:
    _, dp = get_bot_and_dispatcher(settings)
    return dp
