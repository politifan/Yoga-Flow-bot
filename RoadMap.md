# RoadMap по проекту Yoga-Flow-bot

## 1. Текущее состояние репозитория
```
LICENSE
README.md
example/
  consultations.json  # пустой список консультаций
  plans.json          # примеры тарифов (Beginner, Sunrise, Strong)
  subscriptions.json  # примеры подписок со статусом pending
  users.json          # примеры пользователей с avatar и phone/email
```
Данных и кода бэкенда/бота нет: стартуем с чистого каркаса.

## 2. Цель и границы сервиса
- Отдельный интеграционный сервис на Python 3.11+ (FastAPI + Aiogram v3).
- Хранения БД нет: все сущности (пользователи, тарифы, подписки, транзакции, курсы, созвоны) живут в Core API основного сайта.
- Сервис связывает: сайт → интеграционный слой → платёжка (sandbox, RUB) → Core API и Telegram-бот.
- Отдаёт пользователю в боте статус подписки, доступные курсы, календарь созвонов и квитанции.

## 3. Целевая архитектура
- **FastAPI-приложение**: REST для сайта, webhook платёжного провайдера, вспомогательные сервисные ручки.
- **Aiogram-бот**: работает в том же процессе; общается с FastAPI (локально) и Core API.
- **Core API (внешний)**: все CRUD по пользователям/тарифам/подпискам/транзакциям/курсам/созвонам, авторизация по service token.
- **PaymentGateway** (абстракция): `create_payment`, `verify_webhook`, `get_payment_status`; реализуем sandbox-провайдера позже меняем на боевой.
- **Интеграционные потоки**:
  - Привязка Telegram: сайт получает `link_token` → пользователь жмёт deeplink → бот отправляет токен в Core API → привязка.
  - Оплата (сайт/бот): создаём транзакцию в Core API → создаём платёж → обновляем транзакцию `provider_payment_id` → платёжка шлёт webhook → обновляем транзакцию → при `SUCCESS` создаём/продлеваем подписку и шлём квитанцию в бот.
  - Просмотр статуса/курсов/созвонов: бот узнаёт `user_id` по Telegram и тянет данные из Core API.

## 4. Технические требования
- FastAPI, Aiogram v3, HTTP JSON, стандартный `logging`.
- Конфигурация через `.env`/переменные: `SERVICE_TOKEN`, `PAYMENT_SECRET`, `PAYMENT_BASE_URL`, `BOT_TOKEN`, `CORE_API_BASE_URL`, `PAYMENT_GATEWAY` и т.д.
- HTTPS для внешних вызовов; проверка подписи webhook; опциональное ограничение IP.
- Валюта по умолчанию: RUB; sandbox режим платёжки.

## 5. Контракты (ожидаемые)
- Core API (внешний): `GET /core/users/{id}`, `GET /core/users/by_telegram/{tg_id}`, `POST /core/users/{id}/telegram/link`, `GET /core/tariffs`, `POST /core/transactions`, `PATCH /core/transactions/{id}`, `GET /core/subscriptions/by_user/{id}`, `POST /core/subscriptions`, `GET /core/courses/available?user_id=...`, `GET /core/calls/upcoming?user_id=...`.
- Интеграционный сервис (для сайта/бота): `POST /api/v1/telegram/link-token`, `POST /api/v1/subscriptions/create_payment_session`, `POST /api/v1/payments/webhook`, `POST /api/v1/transactions/{id}/send_receipt`, `GET /health`.
- PaymentGateway: интерфейс из ТЗ (`create_payment`, `verify_webhook`, `get_payment_status`).

## 6. План работ (итерации)
1) **Подготовка окружения**
   - Завести venv/poetry, базовый `pyproject.toml`/`requirements.txt`.
   - Настроить `.env.example`, базовый `logging` формат (JSON/текст).

2) **Каркас проекта**
   - Каталоги `app/api`, `app/bot`, `app/core_client`, `app/payments`, `app/config`, `app/models` (pydantic-схемы), `app/services`.
   - Healthcheck `/health`, базовая зависимость конфигурации и логгера.

3) **Клиент Core API**
   - HTTP-клиент с авторизацией по service token.
   - Pydantic-модели запросов/ответов; обработка ошибок (`code`, `message`, `details`).
   - Методы для всех ожидаемых ручек (users/tariffs/transactions/subscriptions/courses/calls).

4) **Абстракция платёжки**
   - Описать `PaymentGateway` интерфейс и `PaymentInitResult/WebhookData/PaymentStatus` модели.
   - Реализовать sandbox-провайдера (пока без реальной интеграции — mock/stub с генерацией `payment_url`, проверкой подписи, хранением статусов в памяти/файле).
   - Точки расширения под боевой провайдер (ключи, endpoints, TLS).

5) **API для сайта/бота**
   - `POST /api/v1/telegram/link-token`: генерация link_token (хранить временно в in-memory/redis? — пока in-memory + TTL).
   - `POST /api/v1/subscriptions/create_payment_session`: валидация тарифа через Core API, создание транзакции, вызов платёжки, обновление транзакции `provider_payment_id`, возврат `payment_url` + `transaction_id`.
   - Обработчики ошибок и единый формат ответов/логов.

6) **Webhook платёжного провайдера**
   - `POST /api/v1/payments/webhook`: верификация подписи, поиск транзакции по `provider_payment_id` (через Core API), обновление статуса.
   - При `SUCCESS`: запрос тарифа, расчёт `expires_at`, создание/обновление подписки в Core API, постановка задач на уведомление/квитанцию.
   - Идемпотентность webhook (проверка текущего статуса в Core API; игнор дублей).

7) **Telegram-бот (Aiogram v3)**
   - Настроить webhook или polling (для dev — polling, prod — webhook `/bot/webhook`).
   - Команды: `/start` с `start_param` (link_token), главное меню (reply keyboard), inline-кнопки тарифов.
   - Сценарии: привязка, просмотр подписки, выбор тарифа и получение `payment_url`, просмотр курсов, календарь созвонов, помощь.
   - FSM для выбора тарифа/оплаты и навигации; обработка неподдерживаемых команд.

8) **Квитанции**
   - Текстовая квитанция (обязательная) с данными транзакции/тарифа/email.
   - Опциональный PDF (например, reportlab), генерация на лету; отправка в Telegram.
   - `POST /api/v1/transactions/{id}/send_receipt` для триггера отправки.

9) **Безопасность и настройка**
   - HTTPS для внешних вызовов; секреты в env; проверка подписи webhook; ограничение IP (опционально).
   - Rate limiting/anti-spam в боте (простые счётчики).
   - Логирование ключевых событий (user_id, transaction_id, statuses, raw_payload для webhook).

10) **Тестирование (ручное, без фреймворков)**
    - Скрипты `if __name__ == "__main__":` для интеграционных вызовов.
    - Чек-лист сценариев (см. ниже) + примеры данных из `example/` для прогонов.
    - Логи как источник верификации входов/выходов.

11) **Документация и развёртывание**
    - Обновить README: запуск dev (uvicorn + bot), пример `.env`.
    - Swagger/Redoc от FastAPI.
    - Контейнеризация (Dockerfile, docker-compose) с env и webhook URL.
    - Инструкции по переключению платёжного провайдера (sandbox → prod).

## 7. Ручные тест-сценарии (минимум)
- Успешная оплата через сайт (создание транзакции → webhook SUCCESS → подписка активна → квитанция отправлена).
- Неуспешная оплата через сайт (FAILED) — статус транзакции и отсутствие подписки.
- Успешная оплата через бота (flow с выбором тарифа).
- Повторный webhook (идемпотентность, статус не меняется повторно).
- Некорректная подпись webhook (ошибка и лог).
- Пользователь без привязки Telegram (подсказка, как привязать).
- Просмотр подписки со статусами `ACTIVE/EXPIRED/PENDING`.
- Отображение курсов и созвонов при разных тарифах.

## 8. Риски и вопросы
- Core API контракт может отличаться — нужны реальные схемы/ошибки и TTL для link_token.
- Выбор конкретного платёжного провайдера влияет на подписи, статусы и поля webhook.
- Где хранить state (link_token, кэш тарифов): in-memory vs Redis; для прод лучше Redis.
- Доставка сообщений Telegram: обработка rate limit и повторов при неуспехе.

## 9. Следующие шаги
1. Утвердить контракт с Core API (URLs, схемы, коды ошибок).
2. Выбрать/зафиксировать sandbox платёжного провайдера и формат подписей.
3. Поднять каркас (шаги 1–3) и заглушку платёжки.
4. Реализовать критический путь оплаты (создание транзакции → webhook → подписка) и привязку Telegram.
5. Добавить бота и основные команды, затем квитанции и полные сценарии тестов.
