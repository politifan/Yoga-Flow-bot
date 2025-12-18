import asyncio
import html
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties

from storage import BOT_DATA_DIR, detect_external_data_dir, load_json, save_json

USERS_FILE = "users.json"
SUBSCRIPTIONS_FILE = "subscriptions.json"
PLANS_FILE = "plans.json"

EXTERNAL_DATA_DIR = detect_external_data_dir(strict=True)
USER_DATA_DIR = EXTERNAL_DATA_DIR
SUBS_DATA_DIR = EXTERNAL_DATA_DIR
COURSE_DATA_DIR = EXTERNAL_DATA_DIR

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

router = Router()


def parse_admin_ids() -> List[int]:
    raw = os.getenv("ADMIN_IDS", "")
    result: List[int] = []
    for chunk in raw.replace(";", ",").split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            result.append(int(chunk))
        except ValueError:
            logger.warning("Skip invalid admin id: %s", chunk)
    return result


ADMIN_IDS = set(parse_admin_ids())


def ensure_data_defaults() -> None:
    # Пользователи — в общем data каталоге Yoga_Flow
    if not (USER_DATA_DIR / USERS_FILE).exists():
        save_json(USERS_FILE, [], base_dir=USER_DATA_DIR)

    # Подписки/заявки — только существующий файл в Yoga_Flow/data
    subs_path = SUBS_DATA_DIR / SUBSCRIPTIONS_FILE
    if not subs_path.exists():
        raise RuntimeError(
            f"Файл подписок {subs_path} не найден. "
            f"Используйте существующий subscriptions.json из проекта Yoga_Flow/data "
            f"или укажите путь через YOGA_DATA_DIR."
        )

    # Курсы/тарифы — берутся из Yoga_Flow/data/plans.json, файл должен существовать
    plans_path = COURSE_DATA_DIR / PLANS_FILE
    if not plans_path.exists():
        raise RuntimeError(
            f"Файл тарифов/курсов {plans_path} не найден. "
            f"Скопируйте {PLANS_FILE} из проекта Yoga_Flow/data или укажите путь через YOGA_DATA_DIR."
        )


async def ensure_admin(message: Message) -> bool:
    user_id = message.from_user.id if message.from_user else None
    if ADMIN_IDS and user_id not in ADMIN_IDS:
        await message.answer("Нет доступа. Добавьте свой id в ADMIN_IDS.")
        return False
    return True


def find_user(users: List[Dict[str, Any]], user_id: str) -> Optional[Dict[str, Any]]:
    return next(
        (u for u in users if str(u.get("user_id") or u.get("id")) == str(user_id)),
        None,
    )


def iso_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def parse_args(command: Optional[CommandObject]) -> List[str]:
    if not command or not command.args:
        return []
    return [arg for arg in command.args.split() if arg]


def esc(value: Any) -> str:
    return html.escape(str(value)) if value is not None else "-"


@router.message(Command("start", "help"))
async def start(message: Message) -> None:
    if not await ensure_admin(message):
        return
    text = (
        "<b>✨ Админ-панель Yoga Flow</b>\n"
        "Управляйте подписками, тарифами и оплатами.\n"
        "────────────\n"
        "<b>Команды</b>\n"
        "• /prolong <code>user_id days</code> — продлить тариф\n"
        "• /approve <code>subscription_id</code> — одобрить оплату/подписку\n"
        "• /contact <code>user_id</code> — контакты пользователя\n"
        "• /recent — последние подписки/заявки\n"
        "• /course — тарифы/курсы\n"
        "• /update_course <code>plan_id field value</code> — изменить курс/тариф\n"
        "────────────\n"
        "Подсказка: поля тарифов — name, price_usd/price, tagline/description, "
        "features_add, features_set (через запятую)."
    )
    await message.answer(text)


@router.message(Command("prolong"))
async def prolong(message: Message, command: CommandObject) -> None:
    if not await ensure_admin(message):
        return
    args = parse_args(command)
    if len(args) < 2:
        await message.answer("⚠️ Формат: /prolong <code>user_id days</code>")
        return

    user_id, days_raw = args[0], args[1]
    try:
        days = int(days_raw)
    except ValueError:
        await message.answer("⚠️ Дни должны быть числом.")
        return

    users = load_json(USERS_FILE, [], base_dir=USER_DATA_DIR)
    user = find_user(users, user_id)
    if not user:
        await message.answer("⚠️ Пользователь не найден.")
        return

    expiry_raw = user.get("tariff_expiry")
    try:
        base_dt = datetime.fromisoformat(expiry_raw.replace("Z", "+00:00")) if expiry_raw else datetime.utcnow()
    except Exception:
        base_dt = datetime.utcnow()

    new_expiry = base_dt + timedelta(days=days)
    user["tariff_expiry"] = new_expiry.isoformat()
    save_json(USERS_FILE, users, base_dir=USER_DATA_DIR)
    await message.answer(
        "✅ Тариф продлён\n"
        f"<b>Пользователь:</b> <code>{esc(user_id)}</code>\n"
        f"<b>На дней:</b> {days}\n"
        f"<b>Новая дата:</b> <code>{esc(user['tariff_expiry'])}</code>"
    )


@router.message(Command("approve"))
async def approve(message: Message, command: CommandObject) -> None:
    if not await ensure_admin(message):
        return
    args = parse_args(command)
    if not args:
        await message.answer("⚠️ Формат: /approve <code>subscription_id</code>")
        return

    sub_id = args[0]
    subs = load_json(SUBSCRIPTIONS_FILE, [], base_dir=SUBS_DATA_DIR)
    sub = next((s for s in subs if str(s.get("id")) == sub_id), None)
    if not sub:
        await message.answer("⚠️ Подписка не найдена.")
        return

    sub["status"] = "active"
    sub["approved_at"] = iso_now()
    save_json(SUBSCRIPTIONS_FILE, subs, base_dir=SUBS_DATA_DIR)
    await message.answer(
        "✅ Оплата/подписка одобрена\n"
        f"<b>ID:</b> <code>{esc(sub_id)}</code>\n"
        f"<b>Пользователь:</b> <code>{esc(sub.get('user_id'))}</code>\n"
        f"<b>План:</b> <code>{esc(sub.get('plan_id'))}</code>\n"
        f"<b>Статус:</b> <code>{esc(sub.get('status'))}</code>"
    )


@router.message(Command("contact"))
async def contact(message: Message, command: CommandObject) -> None:
    if not await ensure_admin(message):
        return
    args = parse_args(command)
    if not args:
        await message.answer("⚠️ Формат: /contact <code>user_id</code>")
        return

    user_id = args[0]
    users = load_json(USERS_FILE, [], base_dir=USER_DATA_DIR)
    user = find_user(users, user_id)
    if not user:
        await message.answer("⚠️ Пользователь не найден.")
        return

    lines = [
        "👤 <b>Контакты пользователя</b>",
        f"<b>ID:</b> <code>{esc(user.get('user_id') or user.get('id'))}</code>",
        f"<b>Имя:</b> {esc(user.get('username') or user.get('name', '-'))}",
        f"<b>Телефон:</b> {esc(user.get('phone', '-'))}",
        f"<b>Email:</b> {esc(user.get('email', '-'))}",
        f"<b>Тариф до:</b> <code>{esc(user.get('tariff_expiry', '-'))}</code>",
    ]
    await message.answer("\n".join(lines))


@router.message(Command("recent"))
async def recent(message: Message) -> None:
    if not await ensure_admin(message):
        return
    subs = load_json(SUBSCRIPTIONS_FILE, [], base_dir=SUBS_DATA_DIR)
    sorted_subs = sorted(subs, key=lambda r: r.get("created_at", ""), reverse=True)
    if not sorted_subs:
        await message.answer("ℹ️ Подписок/заявок нет.")
        return

    lines = []
    for sub in sorted_subs[:5]:
        lines.append(
            f"• <b>ID:</b> <code>{esc(sub.get('id'))}</code> | "
            f"<b>User:</b> <code>{esc(sub.get('user_id'))}</code> | "
            f"<b>План:</b> <code>{esc(sub.get('plan_id'))}</code>\n"
            f"  <b>Статус:</b> <code>{esc(sub.get('status'))}</code> | "
            f"<b>Создано:</b> <code>{esc(sub.get('created_at'))}</code> | "
            f"<b>До:</b> <code>{esc(sub.get('ends_at'))}</code>"
        )
    await message.answer("<b>Последние подписки/заявки:</b>\n" + "\n".join(lines))


@router.message(Command("course"))
async def course(message: Message) -> None:
    if not await ensure_admin(message):
        return
    plans = load_json(PLANS_FILE, [], base_dir=COURSE_DATA_DIR)
    if not plans:
        await message.answer("ℹ️ Планы/курсы не найдены в plans.json.")
        return

    lines = ["<b>Тарифы/курсы:</b>"]
    for plan in plans:
        line = (
            f"• <b>{esc(plan.get('name', '-'))}</b> "
            f"(<code>{esc(plan.get('id', '?'))}</code>) — "
            f"${esc(plan.get('price_usd', 0))}\n"
            f"  {esc(plan.get('tagline', '-'))}"
        )
        lines.append(line)
        features = plan.get("features") or []
        for feat in features[:4]:
            lines.append(f"  · {esc(feat)}")
    await message.answer("\n".join(lines))


@router.message(Command("update_course"))
async def update_course(message: Message, command: CommandObject) -> None:
    if not await ensure_admin(message):
        return
    args = parse_args(command)
    if len(args) < 3:
        await message.answer(
            "<b>Формат:</b> /update_course <code>plan_id field value</code>\n"
            "Поля: <code>name</code> | <code>price_usd</code> (или price) | <code>tagline</code> (или description) | "
            "<code>features_add</code> | <code>features_set</code>\n"
            "Для features_* значения перечисляйте через запятую."
        )
        return

    plan_id, field = args[0], args[1]
    value_raw = " ".join(args[2:])

    plans = load_json(PLANS_FILE, [], base_dir=COURSE_DATA_DIR)
    plan = next((p for p in plans if str(p.get("id")) == plan_id), None)
    if not plan:
        await message.answer("⚠️ План не найден.")
        return

    try:
        if field in ("name",):
            plan["name"] = value_raw
        elif field in ("price_usd", "price"):
            plan["price_usd"] = float(value_raw)
        elif field in ("tagline", "description"):
            plan["tagline"] = value_raw
        elif field == "features_add":
            new_features = [v.strip() for v in value_raw.split(",") if v.strip()]
            plan.setdefault("features", [])
            plan["features"].extend(new_features)
        elif field == "features_set":
            plan["features"] = [v.strip() for v in value_raw.split(",") if v.strip()]
        else:
            await message.answer(
                "⚠️ Неизвестное поле. Используйте name | price_usd | tagline | features_add | features_set"
            )
            return
    except ValueError:
        await message.answer("⚠️ Неверное значение для поля.")
        return

    save_json(PLANS_FILE, plans, base_dir=COURSE_DATA_DIR)
    await message.answer(
        "✅ Тариф/курс обновлён\n"
        f"<b>Plan:</b> <code>{esc(plan_id)}</code>\n"
        f"<b>Поле:</b> <code>{esc(field)}</code>\n"
        f"<b>Новое значение:</b> {esc(value_raw)}"
    )


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def main() -> None:
    ensure_data_defaults()
    token = os.getenv("ADMIN_BOT_TOKEN")
    if not token:
        raise RuntimeError("Переменная окружения ADMIN_BOT_TOKEN не задана.")
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = build_dispatcher()
    logger.info("Админ-бот (aiogram) запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
