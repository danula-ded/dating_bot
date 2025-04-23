import aio_pika
import msgpack
from aio_pika import ExchangeType
from aiogram import types
from aiogram.fsm.context import FSMContext
from starlette_context import context
from starlette_context.header_keys import HeaderKeys

from src.handlers.states.file import FileStates
from src.logger import logger
from src.metrics import TOTAL_SEND_MESSAGES, measure_time
from src.schema.file import FileMessage
from src.storage.rabbit import channel_pool


async def initiate_upload(message: types.Message, state: FSMContext) -> None:
    if message.from_user is None:
        logger.error('Ошибка: сообщение не содержит информации об отправителе (from_user = None).')
        return

    # Устанавливаем состояние через FSMContext
    await state.set_state(FileStates.waiting_for_file)
    await message.reply('Отправьте файл или фотографию, которые хотите загрузить.')


async def check_state(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    await message.reply(f"Текущее состояние: {current_state or 'Нет состояния'}")


@measure_time('show_files')
async def show_files(message: types.Message) -> None:
    """Кладёт информацию о пользователе в очередь."""
    if message.from_user is None:
        logger.error('Ошибка: сообщение не содержит информации об отправителе (from_user = None).')
        return

    async with channel_pool.acquire() as channel:
        # Объявляем обменник и очередь
        exchange = await channel.declare_exchange('user_files', ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue('user_messages', durable=True)
        await queue.bind(exchange, 'user_messages')

        await exchange.publish(
            aio_pika.Message(
                msgpack.packb(FileMessage(user_id=message.from_user.id, action='show_files_user').model_dump()),
                correlation_id=context.get(HeaderKeys.correlation_id),
            ),
            routing_key='user_messages',
        )
    TOTAL_SEND_MESSAGES.labels(operation='show_files').inc()
