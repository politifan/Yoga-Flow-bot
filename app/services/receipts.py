from datetime import datetime
from typing import Optional, Tuple

from app.core_client import CoreAPIClient, Tariff, Transaction, User


class ReceiptService:
    def __init__(self, core: CoreAPIClient):
        self.core = core

    async def _find_tariff(self, tariff_id: str) -> Optional[Tariff]:
        tariffs = await self.core.get_tariffs()
        for t in tariffs:
            if t.id == tariff_id:
                return t
        return None

    async def build_text_receipt(self, transaction_id: str) -> Tuple[str, User]:
        tx: Transaction = await self.core.get_transaction(transaction_id)
        user: User = await self.core.get_user(tx.user_id)
        tariff = await self._find_tariff(tx.tariff_id)

        lines = [
            "Квитанция по оплате",
            f"Транзакция: {tx.id}",
            f"Дата: {datetime.utcnow().isoformat()}",
            f"Пользователь: {user.email or user.id}",
            f"Тариф: {tariff.name if tariff else tx.tariff_id}",
            f"Сумма: {tx.amount} {tx.currency}",
            f"Статус: {tx.status.value}",
        ]
        if tx.provider_payment_id:
            lines.append(f"Платежка ID: {tx.provider_payment_id}")
        return "\n".join(lines), user
