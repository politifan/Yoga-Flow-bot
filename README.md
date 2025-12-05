# Yoga-Flow-bot

Интеграционный сервис (FastAPI + Aiogram) между сайтом, платежкой и Telegram-ботом.

## Запуск в разработке
1. Python 3.11+
2. Установите зависимости: `pip install -r requirements.txt`
3. Скопируйте `.env.example` в `.env` и задайте токены.
4. Запустите API: `uvicorn app.main:app --reload`
5. Для локального теста бота используйте `python -m app` (polling/webhook будет добавлен позже).

## Структура
- `app/main.py` — FastAPI-приложение, подключение роутов.
- `app/api/routes/health.py` — healthcheck `/health`.
- `app/bot/` — каркас бота (Aiogram v3).
- `app/core_client/` — HTTP-клиент Core API.
- `app/payments/` — абстракция платёжного провайдера и sandbox-заглушка.
- `app/config.py` — настройки через переменные окружения.
- `example/` — примеры данных (тарифы, пользователи, подписки, консультации).

Дальнейшие шаги описаны в `RoadMap.md`.
