from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Моя подписка"),
            KeyboardButton(text="Оплатить / продлить"),
        ],
        [
            KeyboardButton(text="Мои курсы"),
            KeyboardButton(text="Календарь созвонов"),
        ],
        [
            KeyboardButton(text="Помощь"),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню",
)
