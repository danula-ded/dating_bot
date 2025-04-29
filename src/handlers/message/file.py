import aio_pika
import msgpack
from aio_pika import ExchangeType
from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ContentType
from starlette_context import context
from starlette_context.header_keys import HeaderKeys

from src.handlers.states.auth import AuthGroup
from src.handlers.states.file import FileStates
from src.logger import logger
from src.metrics import TOTAL_SEND_MESSAGES, measure_time
from src.schema.file import FileMessage
from src.schema.profile import ProfileCreate
from src.schema.registration import RegistrationMessage
from src.schema.user import UserCreate
from src.storage.minio_client import check_minio_connection, get_file_path, upload_file
from src.storage.rabbit import channel_pool

from .router import router


def shorten_file_name(file_name: str, max_length: int = 32) -> str:
    if len(file_name) <= max_length:
        return file_name
    name, extension = file_name.rsplit('.', 1)
    remaining_length = max_length - len(extension) - 1 - 4
    start_length = remaining_length
    shortened_name = f'{name[:start_length]}***{name[-4:]}.{extension}'
    return shortened_name


@router.message(F.content_type == ContentType.DOCUMENT)
@measure_time('handle_file_upload')
async def handle_file_upload(message: types.Message, state: FSMContext) -> None:
    """
    Обрабатывает файл в двух случаях:
    1. Когда пользователь в состоянии FileStates.waiting_for_file (команда /upload)
    2. Когда пользователь в состоянии AuthGroup.registration_photo (процесс регистрации)
    """
    # Проверяем текущее состояние пользователя
    current_state = await state.get_state()

    # Проверяем только нужные состояния
    if current_state not in [FileStates.waiting_for_file.state, AuthGroup.registration_photo.state]:
        await message.reply('Ваш запрос некорректен. Используйте команду для загрузки файла.')
        return

    if message.from_user is None:
        logger.error('Ошибка: сообщение не содержит информации об отправителе (from_user = None).')
        return

    # Проверяем соединение с MinIO
    if not check_minio_connection():
        await message.reply('Ошибка: сервис хранения файлов недоступен.')
        return

    from src.bot import bot

    if not message.document:
        await message.reply('Пожалуйста, отправьте файл.')
        return

    document = message.document
    file_info = await bot.get_file(document.file_id)
    if file_info.file_path is None or document.file_name is None:
        logger.error('Ошибка: не удалось получить информацию о файле. ID файла: %s', document.file_id)
        await message.reply('Ошибка при получении информации о файле.')
        return

    file_bytes = await bot.download_file(file_info.file_path)
    if file_bytes is None:
        logger.error('Ошибка: не удалось скачать файл.')
        await message.reply('Ошибка при скачивании файла.')
        return

    user_id = message.from_user.id
    file_name = shorten_file_name(document.file_name)

    try:
        unique_name = upload_file(user_id, file_name, file_bytes.read())
        logger.info('Файл %s загружен. ID пользователя: %s. Путь к файлу: %s', file_name, user_id, unique_name)

        # Подключаемся к очереди
        async with channel_pool.acquire() as channel:
            # Объявляем обменник и очередь
            exchange = await channel.declare_exchange('user_files', ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue('user_messages', durable=True)
            await queue.bind(exchange, 'user_messages')

            if current_state == FileStates.waiting_for_file.state:
                # Обработка обычной загрузки файла
                await exchange.publish(
                    aio_pika.Message(
                        msgpack.packb(
                            FileMessage(
                                user_id=message.from_user.id,
                                action='upload_file',
                                file_name=file_name,
                            ).model_dump()
                        ),
                        correlation_id=context.get(HeaderKeys.correlation_id),
                    ),
                    routing_key='user_messages',
                )
                TOTAL_SEND_MESSAGES.labels(operation='upload_file').inc()
                await state.clear()
                await message.reply(f'Файл {file_name} успешно загружен!')

            elif current_state == AuthGroup.registration_photo.state:
                # Проверяем, что это изображение только для регистрации
                if not document.mime_type.startswith('image/'):
                    await message.reply('Пожалуйста, отправьте изображение для профиля.')
                    return

                # Обработка фото для регистрации
                photo_url = get_file_path(unique_name)
                user_data = await state.get_data()
                logger.info('Creating user with data: %s', user_data)

                try:
                    user = UserCreate(
                        user_id=user_id,
                        username=message.from_user.username or f'user_{user_id}',
                        first_name=user_data['first_name'],
                        age=user_data['age'],
                        gender=user_data['gender'],
                        city_name=user_data.get('city_name', 'Не указан'),
                        bio=user_data['bio'],
                        photo_url=photo_url,
                    )

                    profile = ProfileCreate(
                        user_id=user_id,
                        bio=user_data['bio'],
                        photo_url=photo_url,
                        preferred_gender=user_data.get('preferred_gender'),
                        preferred_age_min=user_data.get('preferred_age_min'),
                        preferred_age_max=user_data.get('preferred_age_max'),
                    )

                    logger.info(
                        '[%s] Registration message received: user=%s profile=%s action=%s',
                        context.get(HeaderKeys.correlation_id),
                        user,
                        profile,
                        'user_registration',
                    )

                    await exchange.publish(
                        aio_pika.Message(
                            body=msgpack.packb(
                                RegistrationMessage(
                                    user=user, profile=profile, correlation_id=context.get(HeaderKeys.correlation_id)
                                ).model_dump()
                            ),
                            content_type='application/x-msgpack',
                            headers={'correlation_id': context.get(HeaderKeys.correlation_id)},
                        ),
                        routing_key='user_messages',
                    )
                    TOTAL_SEND_MESSAGES.labels(operation='registration').inc()
                    await state.clear()
                    await message.reply('Спасибо за регистрацию!')
                except Exception as e:
                    logger.error('Ошибка при создании пользователя: %s', e)
                    await message.reply('Произошла ошибка при обработке данных. Пожалуйста, попробуйте еще раз.')

    except Exception as e:
        logger.error('Ошибка при загрузке файла: %s', e)
        await message.reply('Произошла ошибка при загрузке файла. Пожалуйста, попробуйте еще раз.')
