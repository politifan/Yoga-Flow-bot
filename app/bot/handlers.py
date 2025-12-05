from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message


async def handle_start(message: Message) -> None:
    await message.answer(
        "Yoga Flow bot готовится к запуску.\n"
        "Скоро здесь появится привязка аккаунта, оплата и расписание."
    )


def register_handlers(dp: Dispatcher) -> None:
    dp.message.register(handle_start, CommandStart())
