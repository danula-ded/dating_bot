import logging
from typing import Any, Dict

import aio_pika
from aio_pika import ExchangeType
from aiogram import types
from aiogram.fsm.context import FSMContext

from src.handlers.states.auth import AuthGroup
from src.storage.minio_client import check_minio_connection
from src.storage.rabbit import channel_pool

logger = logging.getLogger(__name__)


async def check_state(message: types.Message, state: FSMContext) -> None:
    """Проверка текущего состояния пользователя и данных регистрации"""
    current_state = await state.get_state()
    state_data = await state.get_data()

    # Форматируем данные состояния для вывода
    state_info = [
        'Текущее состояние бота:',
        f'- Состояние: {current_state or "Не установлено"}',
        '',
        'Собранные данные:',
    ]

    # Добавляем собранные данные, если они есть
    if state_data:
        for key, value in state_data.items():
            state_info.append(f'- {key}: {value}')
    else:
        state_info.append('- Данные отсутствуют')

    await message.reply('\n'.join(state_info))


async def check_services(message: types.Message) -> None:
    """Проверка состояния сервисов (RabbitMQ, MinIO)"""
    status_info = ['Статус сервисов:']

    # Проверяем RabbitMQ
    try:
        async with channel_pool.acquire() as channel:
            await channel.declare_exchange('test_exchange', ExchangeType.TOPIC)
            status_info.append('✅ RabbitMQ: Работает')
    except Exception as e:
        logger.error('RabbitMQ check failed: %s', e)
        status_info.append('❌ RabbitMQ: Ошибка подключения')

    # Проверяем MinIO
    try:
        if check_minio_connection():
            status_info.append('✅ MinIO: Работает')
        else:
            status_info.append('❌ MinIO: Ошибка подключения')
    except Exception as e:
        logger.error('MinIO check failed: %s', e)
        status_info.append('❌ MinIO: Ошибка подключения')

    await message.reply('\n'.join(status_info))


async def debug_info(message: types.Message, state: FSMContext) -> None:
    """Получение расширенной отладочной информации"""
    debug_data: Dict[str, Any] = {
        'user_id': message.from_user.id,
        'chat_id': message.chat.id,
        'current_state': await state.get_state(),
        'state_data': await state.get_data(),
        'is_private': message.chat.type == 'private',
    }

    debug_info = [
        'Отладочная информация:',
        f'- ID пользователя: {debug_data["user_id"]}',
        f'- ID чата: {debug_data["chat_id"]}',
        f'- Тип чата: {message.chat.type}',
        f'- Текущее состояние: {debug_data["current_state"]}',
        '',
        'Данные состояния:',
    ]

    if debug_data['state_data']:
        for key, value in debug_data['state_data'].items():
            debug_info.append(f'- {key}: {value}')
    else:
        debug_info.append('- Данные отсутствуют')

    logger.info('Debug info requested for user %s: %s', message.from_user.id, debug_data)
    await message.reply('\n'.join(debug_info))
