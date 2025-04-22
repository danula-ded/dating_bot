import logging

from aiogram import types
from aiogram.fsm.context import FSMContext

from src.handlers.states.auth import AuthGroup

logger = logging.getLogger(__name__)


# Функция обработки команды /start
async def start(message: types.Message, state: FSMContext) -> None:
    await state.set_data({})
    current_state = await state.get_state()

    if current_state == AuthGroup.authorized.state:
        await message.reply('Вы уже зарегистрированы! Используйте /help для просмотра доступных команд.')
        return

    await state.set_state(AuthGroup.registration)
    await message.reply(
        'Добро пожаловать в бот знакомств! Давайте начнем регистрацию.\n' 'Пожалуйста, введите ваше имя:'
    )


# функция обработки команды /help
async def help_command(message: types.Message) -> None:
    commands = (
        '/help - показать доступные команды',
        '/upload - загрузить файл',
        '/show_files - отобразить файлы',
        '/check_state - проверить состояние',
    )
    await message.reply('\n'.join(commands))
