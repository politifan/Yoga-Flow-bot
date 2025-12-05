# Ручной чек-лист (этап 10)

## Базовые проверки API
- `GET /health` → `{status:"ok"}`.
- `POST /api/v1/telegram/link-token` с user_id → 201, получить `link_token`.
- `POST /api/v1/subscriptions/create_payment_session` (валидный user/tariff) → получить `payment_url`, `transaction_id`.
- `POST /api/v1/payments/webhook` (валидный payload и подпись) → статус транзакции обновлён, подписка создана при SUCCESS.
- `POST /api/v1/payments/webhook` повторно с тем же payment_id и SUCCESS → `{message:"already processed"}` без дубля операций.
- `POST /api/v1/payments/webhook` с неверной подписью → 400.
- `POST /api/v1/transactions/{id}/send_receipt` → текст квитанции содержит ID и сумму; если у пользователя есть `telegram_user_id`, сообщение доставлено в Telegram.

## Потоки с ботом (polling)
- `/start <link_token>` → аккаунт привязан, главное меню показано.
- `/start` без токена при непривязанном аккаунте → инструкция как привязать.
- Кнопка «Моя подписка» → корректный статус (`ACTIVE/PENDING/EXPIRED`).
- Кнопка «Оплатить / продлить» → тарифы с ценой, кликаем → бот выдаёт `payment_url`.
- Кнопка «Мои курсы» → список курсов или сообщение об отсутствии.
- Кнопка «Календарь созвонов» → список созвонов или сообщение об отсутствии.

## Сценарии платежей
- Успешная оплата через сайт/бот: payment_session → webhook SUCCESS → транзакция SUCCESS → подписка создана/продлена → квитанция генерируется.
- Неуспешная оплата: webhook FAILED → транзакция FAILED → подписка не создаётся.
- Повторный webhook (SUCCESS/FAILED) → идемпотентный ответ, без двойных обновлений.

## Безопасность и устойчивость
- Вызовы к Core API с неверным токеном → обрабатываются и логируются ошибки `CoreAPIError`.
- Webhook без payment_id → 404 для транзакции.
- Сбои Core API (симуляция 5xx) → ошибки пробрасываются, логи содержат статус и детали.
