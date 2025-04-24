import logging

from aiogram import types
from aiogram.fsm.context import FSMContext

from src.handlers.states.auth import AuthGroup

logger = logging.getLogger(__name__)


# Функция обработки команды /start
async def start(message: types.Message, state: FSMContext) -> None:
    """Handle the /start command"""
    # Очищаем предыдущее состояние и данные
    await state.clear()
    await state.set_data({})
    
    # Устанавливаем начальное состояние регистрации
    await state.set_state(AuthGroup.registration_name)
    current_state = await state.get_state()
    logger.info('State after start: %s', current_state)

    if current_state == AuthGroup.authorized.state:
        await message.reply('Вы уже зарегистрированы! Используйте /help для просмотра доступных команд.')
        return

    await message.reply(
        'Добро пожаловать в бот знакомств! Давайте начнем регистрацию.\n'
        'Пожалуйста, введите ваше имя:'
    )


# функция обработки команды /help
async def help_command(message: types.Message) -> None:
    """Показывает список доступных команд и их описание"""
    commands = (
        '📋 Основные команды:',
        '/start - начать регистрацию в боте',
        '/help - показать это сообщение',
        '/profile - просмотреть и отредактировать свой профиль',
        '',
        '👤 Профиль и настройки:',
        '/edit_profile - редактировать профиль',
        '/preferences - настроить предпочтения для поиска',
        '',
        '🔍 Поиск и знакомства:',
        '/search - найти анкеты для просмотра',
        '',
        '📤 Работа с файлами:',
        '/upload - загрузить фото профиля',
        '/show_files - показать список загруженных файлов',
        '',
        '🔧 Диагностика и отладка:',
        '/check_state - показать текущее состояние и собранные данные',
        '/check_services - проверить состояние сервисов (RabbitMQ, MinIO)',
        '/debug - показать расширенную отладочную информацию',
        '',
        '💡 Подсказка: Используйте /check_state во время регистрации, чтобы увидеть свой прогресс.'
    )
    await message.reply('\n'.join(commands))
