from aiogram import Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.filters.command import CommandObject
from aiogram.types import CallbackQuery, Message

from app.bot.context import BotContext
from app.bot.keyboards import MAIN_MENU
from app.bot.services import BotService
from app.core_client import CoreAPIError


def _get_ctx(message: Message) -> BotContext:
    ctx: BotContext = message.bot["ctx"]
    return ctx


async def handle_start(message: Message, command: CommandObject | None = None) -> None:
    ctx = _get_ctx(message)
    service = BotService(ctx.core, ctx.integration_client)
    deep_link_token = command.args if command else None

    if deep_link_token:
        user_id = ctx.link_tokens.consume(deep_link_token)
        if user_id:
            try:
                await ctx.core.link_telegram(user_id=user_id, telegram_user_id=message.from_user.id, link_token=deep_link_token)
                await message.answer("Аккаунт привязан к Telegram ✅", reply_markup=MAIN_MENU)
            except CoreAPIError as err:
                await message.answer(f"Не удалось привязать аккаунт: {err}")
        else:
            await message.answer("Ссылка недействительна или устарела.")

    user = await service.get_user_by_telegram(message.from_user.id)
    if not user:
        await message.answer(
            "Привет! Чтобы привязать аккаунт, зайдите на сайт и нажмите «Подключить Telegram», затем вернитесь по ссылке.",
            reply_markup=MAIN_MENU,
        )
        return

    subscription = await service.get_subscription(user.id)
    text = service.format_subscription(user, subscription)
    await message.answer(f"Привет, {user.username or 'йог'}!\n\n{text}", reply_markup=MAIN_MENU)


async def handle_subscription(message: Message) -> None:
    ctx = _get_ctx(message)
    service = BotService(ctx.core, ctx.integration_client)
    user = await service.get_user_by_telegram(message.from_user.id)
    if not user:
        await message.answer("Аккаунт не привязан. Зайдите на сайт и подключите Telegram.")
        return

    subscription = await service.get_subscription(user.id)
    text = service.format_subscription(user, subscription)
    await message.answer(text, reply_markup=MAIN_MENU)


async def handle_tariffs(message: Message) -> None:
    ctx = _get_ctx(message)
    service = BotService(ctx.core, ctx.integration_client)
    user = await service.get_user_by_telegram(message.from_user.id)
    if not user:
        await message.answer("Аккаунт не привязан. Зайдите на сайт и подключите Telegram.")
        return

    tariffs = await service.get_tariffs()
    kb = service.tariffs_keyboard(tariffs)
    await message.answer("Выберите тариф, чтобы получить ссылку на оплату:", reply_markup=kb)


async def handle_pay_callback(callback: CallbackQuery) -> None:
    ctx = (callback.message or callback).bot["ctx"]
    service = BotService(ctx.core, ctx.integration_client)
    user = await service.get_user_by_telegram(callback.from_user.id)
    if not user:
        await callback.message.answer("Аккаунт не привязан. Зайдите на сайт и подключите Telegram.")
        await callback.answer()
        return

    tariff_id = callback.data.split("pay:", 1)[1] if callback.data else None
    if not tariff_id:
        await callback.answer("Тариф не выбран", show_alert=True)
        return

    payment_url = await service.create_payment_session(user.id, tariff_id=tariff_id, source="bot")
    if not payment_url:
        await callback.answer("Не удалось создать ссылку", show_alert=True)
        return

    await callback.message.answer(f"Ссылка на оплату: {payment_url}")
    await callback.answer()


async def handle_courses(message: Message) -> None:
    ctx = _get_ctx(message)
    service = BotService(ctx.core, ctx.integration_client)
    user = await service.get_user_by_telegram(message.from_user.id)
    if not user:
        await message.answer("Аккаунт не привязан. Зайдите на сайт и подключите Telegram.")
        return
    courses = await ctx.core.get_available_courses(user.id)
    if not courses:
        await message.answer("Доступных курсов пока нет.", reply_markup=MAIN_MENU)
        return
    lines = [f"• {c.title}" + (f" — {c.url}" if c.url else "") for c in courses]
    await message.answer("Мои курсы:\n" + "\n".join(lines), reply_markup=MAIN_MENU)


async def handle_calls(message: Message) -> None:
    ctx = _get_ctx(message)
    service = BotService(ctx.core, ctx.integration_client)
    user = await service.get_user_by_telegram(message.from_user.id)
    if not user:
        await message.answer("Аккаунт не привязан. Зайдите на сайт и подключите Telegram.")
        return
    calls = await ctx.core.get_upcoming_calls(user.id)
    if not calls:
        await message.answer("Ближайших созвонов нет.", reply_markup=MAIN_MENU)
        return
    lines = [f"• {c.title} — {c.start_at} — {c.discord_link or 'ссылка позже'}" for c in calls]
    await message.answer("Календарь созвонов:\n" + "\n".join(lines), reply_markup=MAIN_MENU)


async def handle_help(message: Message) -> None:
    await message.answer(
        "Помощь:\n- Привяжите аккаунт через ссылку с сайта.\n"
        "- Посмотрите подписку через «Моя подписка».\n"
        "- Для оплаты выберите тариф в «Оплатить / продлить».",
        reply_markup=MAIN_MENU,
    )


def register_handlers(dp: Dispatcher) -> None:
    dp.message.register(handle_start, CommandStart(deep_link=True))
    dp.message.register(handle_subscription, F.text == "Моя подписка")
    dp.message.register(handle_tariffs, F.text == "Оплатить / продлить")
    dp.callback_query.register(handle_pay_callback, F.data.startswith("pay:"))
    dp.message.register(handle_courses, F.text == "Мои курсы")
    dp.message.register(handle_calls, F.text == "Календарь созвонов")
    dp.message.register(handle_help, F.text == "Помощь")
    dp.message.register(handle_help, Command(commands=["help"]))
