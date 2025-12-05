# API контракт (черновик)

## 1. Telegram link-token
- `POST /api/v1/telegram/link-token`
```json
Request: { "user_id": "u_0001" }
Response 201:
{
  "link_token": "abc123",
  "telegram_deeplink": "https://t.me/<bot_username>?start=abc123",
  "expires_at": 1701800000.0
}
```

## 2. Создание платёжной сессии
- `POST /api/v1/subscriptions/create_payment_session`
```json
Request: { "user_id": "u_0001", "tariff_id": "sunrise", "source": "site" }
Response 200:
{
  "transaction_id": "t_0001",
  "payment_url": "https://sandbox-pay.example.com/pay/sandbox_123",
  "provider_payment_id": "sandbox_123",
  "amount": 1200,
  "currency": "RUB"
}
```

## 3. Webhook платёжного провайдера
- `POST /api/v1/payments/webhook`
```json
Request (пример sandbox): {
  "payment_id": "sandbox_123",
  "status": "SUCCESS",
  "amount": 1200,
  "currency": "RUB",
  "metadata": { "user_id": "u_0001", "tariff_id": "sunrise", "transaction_id": "t_0001" }
}
Response 200:
{
  "status": "ok",
  "transaction_id": "t_0001",
  "new_status": "SUCCESS",
  "subscription_id": "s_0001",
  "expires_at": "2025-12-05T12:00:00Z"
}
```
- Повторный webhook с тем же `payment_id` и SUCCESS → `{ "message": "already processed" }`.

## 4. Квитанция
- `POST /api/v1/transactions/{transaction_id}/send_receipt`
```json
Response 200:
{
  "transaction_id": "t_0001",
  "receipt_text": "Квитанция по оплате\nТранзакция: t_0001\n...",
  "delivered_to_telegram": true
}
```

## 5. Webhook бота
- `POST /bot/webhook` — endpoint для Telegram.
- При использовании прод-вебхука нужно выставить `BOT_WEBHOOK_URL=https://<domain>/bot/webhook` и зарегистрировать его (стартап приложения сделает `setWebhook`).
