# Yoga Flow Admin Bot

Простой телеграм-бот для админки: продление тарифов, одобрение оплат, просмотр заявок и управление данными курса/тарифов.

## Быстрый запуск
1. Установите зависимости: `pip install -r requirements.txt` (aiogram 3)
2. Экспортируйте токен и список админов:
   ```
   export ADMIN_BOT_TOKEN=<tg_token>
   export ADMIN_IDS=<id1,id2>   # опционально, через запятую
   export YOGA_DATA_DIR=/path/to/Yoga_Flow/data  # опционально, если путь отличается
   ```
3. Запустите: `python admin_bot.py`

## Команды
- `/start` / `/help` — подсказка
- `/prolong <user_id> <days>` — продлить тариф на дни
- `/approve <subscription_id>` — одобрить оплату/подписку
- `/contact <user_id>` — контакты пользователя
- `/recent` — последние 5 подписок/заявок из `YOGA_DATA_DIR/subscriptions.json`
- `/course` — показать тарифы/курсы из `plans.json` (Yoga_Flow/data)
- `/update_course <plan_id> <field> <value>` — обновить тариф/курс  
  Поля: `name`, `price_usd` (или `price`), `tagline` (или `description`), `features_add`, `features_set` (значения через запятую)

## Данные
- Пользователи: `YOGA_DATA_DIR/users.json` (по умолчанию `../Yoga_Flow/data`).
- Подписки/заявки: `YOGA_DATA_DIR/subscriptions.json` (существующий файл из Yoga_Flow/data; новый не создаётся).
- Тарифы/курсы: `YOGA_DATA_DIR/plans.json` (из проекта Yoga_Flow). Файл обязателен.

## Пользовательский бот (доступ к курсам)
Файл: `user_bot.py` (aiogram). Использует общие данные из `YOGA_DATA_DIR`, хранит токены/связки в общих файлах `YOGA_DATA_DIR/tg_tokens.json` и `YOGA_DATA_DIR/tg_links.json`.

Команды:
- `/start` / `/help` — подсказка
- `/tariffs` — список тарифов/курсов
- `/link <token>` — привязать аккаунт через токен, сгенерированный на сайте
- `/status` — статус подписки для привязанного аккаунта
- `/support` — контакты поддержки

OAuth-связка (сайт → бот):
- На сайте перейдите в `/tg/link` (нужна авторизация, задайте `USER_BOT_USERNAME` в `.env` проекта Yoga_Flow).
- Сгенерируйте токен (действует ~15 минут) и откройте бота по ссылке или командой `/link <token>`.
- Бот помечает связку в `tg_links.json`; токены в `tg_tokens.json`.

Запуск:
```
export USER_BOT_TOKEN=<tg_token_for_users>
export YOGA_DATA_DIR=/path/to/Yoga_Flow/data  # если не рядом
python user_bot.py
```

Данные хранятся в JSON для простоты; их можно заменить интеграцией с БД или API сайта.

## Идея клиентского (пользовательского) бота
- Авторизация по телефону/коду, связываем `telegram_id` с `user_id` из сайта.
- Меню: просмотр тарифов, оплата (ссылка/инвойс), статус подписки, календарь занятий, поддержка.
- Уведомления: напоминания о продлении, новые видео, подтверждение оплаты.
- Технически: тот же storage или REST API сайта; отдельный токен, отдельный `Application` с командами `/tariffs`, `/buy`, `/status`, `/support`.
