import asyncio
import html
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from storage import BOT_DATA_DIR, detect_external_data_dir, load_json, save_json

PLANS_FILE = "plans.json"
SUBSCRIPTIONS_FILE = "subscriptions.json"
USERS_FILE = "users.json"
TG_LINKS_FILE = "tg_links.json"
TG_TOKENS_FILE = "tg_tokens.json"
TOKEN_TTL_MINUTES = 15

EXTERNAL_DATA_DIR = detect_external_data_dir(strict=True)
PLANS_DATA_DIR = EXTERNAL_DATA_DIR
SUBS_DATA_DIR = EXTERNAL_DATA_DIR
USERS_DATA_DIR = EXTERNAL_DATA_DIR
TG_DATA_DIR = EXTERNAL_DATA_DIR

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

router = Router()


def esc(value) -> str:
    return html.escape(str(value)) if value is not None else "-"


def ensure_data_defaults() -> None:
    if not (PLANS_DATA_DIR / PLANS_FILE).exists():
        raise RuntimeError(f"Не найден {PLANS_DATA_DIR / PLANS_FILE}. Укажите YOGA_DATA_DIR.")
    if not (SUBS_DATA_DIR / SUBSCRIPTIONS_FILE).exists():
        raise RuntimeError(f"Не найден {SUBS_DATA_DIR / SUBSCRIPTIONS_FILE}. Укажите YOGA_DATA_DIR.")
    if not (USERS_DATA_DIR / USERS_FILE).exists():
        raise RuntimeError(f"Не найден {USERS_DATA_DIR / USERS_FILE}. Укажите YOGA_DATA_DIR.")
    (TG_DATA_DIR / TG_LINKS_FILE).parent.mkdir(parents=True, exist_ok=True)
    if not (TG_DATA_DIR / TG_LINKS_FILE).exists():
        save_json(TG_LINKS_FILE, [], base_dir=TG_DATA_DIR)
    if not (TG_DATA_DIR / TG_TOKENS_FILE).exists():
        save_json(TG_TOKENS_FILE, [], base_dir=TG_DATA_DIR)


def iso_now() -> str:
    return datetime.utcnow().isoformat() + "Z"


def parse_iso(dt: Optional[str]) -> Optional[datetime]:
    if not dt:
        return None
    try:
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        return None


def load_links() -> List[Dict[str, str]]:
    return load_json(TG_LINKS_FILE, [], base_dir=TG_DATA_DIR)


def save_links(links: List[Dict[str, str]]) -> None:
    save_json(TG_LINKS_FILE, links, base_dir=TG_DATA_DIR)


def load_tokens() -> List[Dict[str, str]]:
    return load_json(TG_TOKENS_FILE, [], base_dir=TG_DATA_DIR)


def save_tokens(tokens: List[Dict[str, str]]) -> None:
    save_json(TG_TOKENS_FILE, tokens, base_dir=TG_DATA_DIR)


def prune_tokens(tokens: List[Dict[str, str]]) -> List[Dict[str, str]]:
    now = datetime.utcnow()
    result = []
    for tok in tokens:
        if tok.get("used_at"):
            continue
        exp = parse_iso(tok.get("expires_at"))
        if not exp or exp <= now:
            continue
        result.append(tok)
    return result


def consume_token(token: str, telegram_id: int) -> Tuple[Optional[Dict[str, str]], str]:
    tokens = prune_tokens(load_tokens())
    match = next((t for t in tokens if t.get("token") == token), None)
    now = datetime.utcnow()
    if not match:
        save_tokens(tokens)
        return None, "invalid"

    exp = parse_iso(match.get("expires_at"))
    if not exp or exp <= now:
        tokens = [t for t in tokens if t.get("token") != token]
        save_tokens(tokens)
        return None, "expired"

    if match.get("used_at"):
        return None, "used"

    match["used_at"] = iso_now()
    match["telegram_id"] = str(telegram_id)
    save_tokens(tokens)

    links = load_links()
    links = [
        l for l in links
        if l.get("telegram_id") != str(telegram_id) and l.get("user_id") != match["user_id"]
    ]
    links.append(
        {
            "telegram_id": str(telegram_id),
            "user_id": match["user_id"],
            "linked_at": iso_now(),
        }
    )
    save_links(links)
    return match, "ok"


def find_link_by_telegram(telegram_id: int) -> Optional[Dict[str, str]]:
    links = load_links()
    return next((l for l in links if str(l.get("telegram_id")) == str(telegram_id)), None)


def get_user_by_id(user_id: str) -> Optional[Dict]:
    users = load_json(USERS_FILE, [], base_dir=USERS_DATA_DIR)
    return next((u for u in users if str(u.get("id") or u.get("user_id")) == str(user_id)), None)


def get_subscriptions(user_id: str) -> List[Dict]:
    subs = load_json(SUBSCRIPTIONS_FILE, [], base_dir=SUBS_DATA_DIR)
    return [s for s in subs if str(s.get("user_id")) == str(user_id)]


async def link_with_token(message: Message, token: str) -> None:
    if not token:
        await message.answer("⚠️ Нужен токен. Получите его на сайте (Dashboard → Link Telegram).")
        return
    record, status = consume_token(token.strip(), message.from_user.id)
    if status == "ok" and record:
        await message.answer(
            "✅ Telegram привязан к аккаунту\n"
            f"<b>User ID:</b> <code>{esc(record['user_id'])}</code>\n"
            f"<b>Telegram ID:</b> <code>{esc(message.from_user.id)}</code>\n"
            "Теперь бот будет показывать ваши подписки."
        )
    elif status == "expired":
        await message.answer("⏳ Токен истёк. Сгенерируйте новый на сайте в разделе «Связать Telegram».")
    elif status == "used":
        await message.answer("⚠️ Токен уже использован. Создайте новый на сайте.")
    else:
        await message.answer("⚠️ Токен недействителен. Сгенерируйте новый на сайте.")


@router.message(Command("start", "help"))
async def start(message: Message, command: CommandObject) -> None:
    token = (command.args or "").strip() if command else ""
    if token:
        await link_with_token(message, token)
        return
    text = (
        "<b>Йога Flow — доступ к курсам</b>\n"
        "Команды:\n"
        "• /tariffs — тарифы и что внутри\n"
        "• /link <code>token</code> — привязать аккаунт через токен с сайта\n"
        "• /status — статус подписки\n"
        "• /support — как связаться с поддержкой\n"
        "Получите токен на сайте в разделе <code>Связать Telegram</code> (Dashboard → Link Telegram)."
    )
    await message.answer(text)


@router.message(Command("tariffs"))
async def tariffs(message: Message) -> None:
    plans = load_json(PLANS_FILE, [], base_dir=PLANS_DATA_DIR)
    if not plans:
        await message.answer("Пока нет тарифов.")
        return
    lines = ["<b>Тарифы</b>"]
    for plan in plans:
        lines.append(
            f"• <b>{esc(plan.get('name', '-'))}</b> "
            f"(<code>{esc(plan.get('id', '?'))}</code>) — ${esc(plan.get('price_usd', 0))}\n"
            f"  {esc(plan.get('tagline', '-'))}"
        )
        for feat in (plan.get("features") or [])[:4]:
            lines.append(f"  · {esc(feat)}")
    await message.answer("\n".join(lines))


@router.message(Command("link"))
async def link_user(message: Message, command: CommandObject) -> None:
    token = (command.args or "").strip() if command else ""
    if not token:
        await message.answer("⚠️ Формат: /link <code>token</code>. Получите токен на сайте в разделе «Связать Telegram».")
        return
    await link_with_token(message, token)


def resolve_user_id(message: Message) -> Optional[str]:
    if not message.from_user:
        return None
    link = find_link_by_telegram(message.from_user.id)
    return link.get("user_id") if link else None


@router.message(Command("status"))
async def status(message: Message) -> None:
    user_id = resolve_user_id(message)
    if not user_id:
        await message.answer(
            "ℹ️ Аккаунт не привязан.\n"
            "Зайдите на сайт → Dashboard → «Связать Telegram», получите токен и отправьте его боту: /link <code>token</code>"
        )
        return

    subs = get_subscriptions(user_id)
    if not subs:
        await message.answer("У вас пока нет активных подписок. Выберите тариф: /tariffs")
        return

    lines = [f"<b>Статус для User ID {esc(user_id)}</b>"]
    for sub in subs:
        lines.append(
            f"• <b>{esc(sub.get('plan_id'))}</b> | "
            f"Статус: <code>{esc(sub.get('status'))}</code> | "
            f"Начало: <code>{esc(sub.get('started_at'))}</code> | "
            f"Действует до: <code>{esc(sub.get('ends_at'))}</code>"
        )
    await message.answer("\n".join(lines))


@router.message(Command("support"))
async def support(message: Message) -> None:
    await message.answer(
        "<b>Поддержка Yoga Flow</b>\n"
        "Почта: support@yogaflow.example\n"
        "Telegram: @your_support_handle\n"
        "Опишите ваш вопрос и укажите user_id для быстрого ответа."
    )


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def main() -> None:
    ensure_data_defaults()
    token = os.getenv("USER_BOT_TOKEN")
    if not token:
        raise RuntimeError("Переменная окружения USER_BOT_TOKEN не задана.")
    bot = Bot(token=token, parse_mode="HTML")
    dp = build_dispatcher()
    logger.info("Пользовательский бот запущен.")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
