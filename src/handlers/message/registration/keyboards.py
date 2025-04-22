from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_registration_keyboard() -> ReplyKeyboardMarkup:
    """Create a keyboard for the registration process"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='Начать регистрацию')],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    return keyboard
