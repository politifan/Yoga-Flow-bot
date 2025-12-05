from typing import Optional

import httpx
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.core_client import CoreAPIClient, Subscription, SubscriptionStatus, Tariff, User


class BotService:
    def __init__(self, core: CoreAPIClient, integration_client: httpx.AsyncClient):
        self.core = core
        self.integration_client = integration_client

    async def get_user_by_telegram(self, telegram_user_id: int) -> Optional[User]:
        return await self.core.get_user_by_telegram(telegram_user_id)

    async def get_subscription(self, user_id: str) -> Optional[Subscription]:
        return await self.core.get_subscription_by_user(user_id)

    async def get_tariffs(self) -> list[Tariff]:
        return await self.core.get_tariffs()

    async def create_payment_session(self, user_id: str, tariff_id: str, source: str = "bot") -> Optional[str]:
        payload = {"user_id": user_id, "tariff_id": tariff_id, "source": source}
        resp = await self.integration_client.post("/subscriptions/create_payment_session", json=payload)
        if resp.status_code >= 400:
            return None
        data = resp.json()
        return data.get("payment_url")

    def tariffs_keyboard(self, tariffs: list[Tariff]) -> InlineKeyboardMarkup:
        buttons = []
        for t in tariffs:
            price = None
            if t.price_rub is not None:
                price = f"{t.price_rub / 100:.0f}₽"
            elif t.price_usd is not None:
                price = f"${t.price_usd}"
            label = f"{t.name}" + (f" — {price}" if price else "")
            buttons.append([InlineKeyboardButton(text=label, callback_data=f"pay:{t.id}")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def format_subscription(self, user: User, subscription: Optional[Subscription]) -> str:
        if not subscription:
            return "Подписка не найдена. Вы можете оформить её через кнопку «Оплатить / продлить»."

        status_map = {
            SubscriptionStatus.ACTIVE: "активна",
            SubscriptionStatus.PENDING: "ожидает оплаты",
            SubscriptionStatus.EXPIRED: "истекла",
        }
        status_label = status_map.get(subscription.status, subscription.status.value)
        expires = subscription.expires_at.isoformat() if subscription.expires_at else "—"
        return (
            f"Подписка: {subscription.tariff_id}\n"
            f"Статус: {status_label}\n"
            f"Истекает: {expires}"
        )
