# Yoga-Flow-bot

Интеграционный сервис (FastAPI + Aiogram) между сайтом, платежкой и Telegram-ботом.

## Запуск в разработке
1. Python 3.11+
2. Установите зависимости: `pip install -r requirements.txt`
3. Скопируйте `.env.example` в `.env` и задайте токены.
4. Запустите API: `uvicorn app.main:app --reload`
5. Для локального теста бота используйте `python -m app.bot.runner` (polling).

## Настройка `.env` (минимум)
- `CORE_API_BASE_URL` — URL Core API (обязательно).
- `SERVICE_TOKEN` — сервисный токен для Core API (обязательно).
- `BOT_TOKEN` — токен Telegram-бота (обязательно).
- `BOT_USERNAME` — username бота (для deeplink, желательно).
- `BOT_WEBHOOK_URL` — внешний URL webhook бота (нужно, если используете webhook вместо polling).
- `PAYMENT_PROVIDER` — идентификатор провайдера, `sandbox` по умолчанию.
- `PAYMENT_BASE_URL` — базовый URL платёжки (опционально для sandbox).
- `PAYMENT_SECRET` — секрет для подписи webhook (обязательно для проверок).
- `PAYMENT_PUBLIC_KEY` — если требуется провайдером (опционально).
- `LOG_LEVEL` — уровень логов (INFO/DEBUG и т.д.).
- `ENVIRONMENT` — метка окружения (local/stage/prod).
- `LINK_TOKEN_TTL_SECONDS` — TTL для link_token (секунды, по умолчанию 900).
- `INTEGRATION_API_BASE_URL` — базовый URL этого сервиса (использует бот для внутренних вызовов).
- `HTTP_MAX_RETRIES`, `HTTP_RETRY_BACKOFF` — число ретраев и бэкофф для вызовов Core API.

## Структура
- `app/main.py` — FastAPI-приложение, подключение роутов.
- `app/api/routes/health.py` — healthcheck `/health`.
- `app/bot/` — каркас бота (Aiogram v3), меню и обработчики.
- `app/core_client/` — HTTP-клиент Core API с pydantic-схемами и обработкой ошибок.
- `app/payments/` — абстракция платёжного провайдера, фабрика и sandbox-заглушка с подписью webhook.
- `app/config.py` — настройки через переменные окружения.
- `app/services/` — link tokens, квитанции.
- `example/` — примеры данных (тарифы, пользователи, подписки, консультации).

## Черновые API (v1)
- `POST /api/v1/telegram/link-token` — выдать link_token + deeplink на бота.
- `POST /api/v1/subscriptions/create_payment_session` — создать транзакцию и платёжную сессию, вернуть `payment_url`.
- `POST /api/v1/payments/webhook` — приём webhook от платёжки, обновление транзакции и создание подписки.
- `POST /api/v1/transactions/{transaction_id}/send_receipt` — сгенерировать текстовую квитанцию и отправить в Telegram (если есть `telegram_user_id`).
- `POST /bot/webhook` — входящий webhook для Telegram (ставьте `BOT_WEBHOOK_URL` на этот путь).

## Бот (Aiogram)
- Команды/кнопки: старт, «Моя подписка», «Оплатить / продлить», «Мои курсы», «Календарь созвонов», «Помощь».
- Привязка по deeplink-токену (`/start <token>`), проверка подписки, получение ссылок на оплату через интеграционный API, вывод курсов и созвонов из Core API.

## Ручной чек-лист
См. `scripts/manual-checklist.md` для прогонов эндпоинтов, webhook идемпотентности и сценариев в боте.

## Прод-развёртывание (без Docker)
- API: `uvicorn app.main:app --host 0.0.0.0 --port 8000` за reverse-proxy (nginx/caddy) с HTTPS.
 - Бот: для простоты polling `python -m app.bot.runner`; для прод — настроить webhook в Telegram на `/bot/webhook` и поднять endpoint в FastAPI (уже есть в приложении).
- HTTPS обязателен для внешних вызовов Core API/платёжки/webhook.
- Проверьте, что переменные `.env` заданы для prod (токены, секреты, реальные URLs, payment provider).

## API примеры
См. `API.md` для примеров запросов/ответов (link-token, create_payment_session, webhook, квитанции, bot webhook).

Дальнейшие шаги описаны в `RoadMap.md`.
