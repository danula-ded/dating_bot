import logging

from aiogram import types
from aiogram.fsm.context import FSMContext

from src.handlers.states.auth import AuthGroup

logger = logging.getLogger(__name__)


# Функция обработки команды /start
async def start(message: types.Message, state: FSMContext) -> None:
    """Handle the /start command"""
    await state.set_data({})
    current_state = await state.get_state()

    if current_state == AuthGroup.authorized.state:
        await message.reply('Вы уже зарегистрированы! Используйте /help для просмотра доступных команд.')
        return

    await state.set_state(AuthGroup.registration_name)
    await message.reply(
        'Добро пожаловать в бот знакомств! Давайте начнем регистрацию.\n' 'Пожалуйста, введите ваше имя:'
    )


# функция обработки команды /help
async def help_command(message: types.Message) -> None:
    """Показывает список доступных команд и их описание"""
    commands = (
        '📋 Основные команды:',
        '/start - начать регистрацию в боте',
        '/help - показать это сообщение',
        '',
        '📤 Работа с файлами:',
        '/upload - загрузить файл',
        '/show_files - показать список загруженных файлов',
        '',
        '🔍 Диагностика и отладка:',
        '/check_state - показать текущее состояние и собранные данные',
        '/check_services - проверить состояние сервисов (RabbitMQ, MinIO)',
        '/debug - показать расширенную отладочную информацию',
        '',
        '💡 Подсказка: Используйте /check_state во время регистрации, чтобы увидеть свой прогресс.',
    )
    await message.reply('\n'.join(commands))
