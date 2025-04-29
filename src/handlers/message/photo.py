import logging

import aio_pika
import msgpack
from aio_pika import ExchangeType
from aiogram import F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ContentType
from starlette_context import context
from starlette_context.header_keys import HeaderKeys

from src.handlers.states.auth import AuthGroup
from src.metrics import TOTAL_SEND_MESSAGES
from src.schema.profile import ProfileCreate
from src.schema.registration import RegistrationMessage
from src.schema.user import UserCreate
from src.storage.minio_client import get_file_path, upload_file
from src.storage.rabbit import channel_pool

from .router import router

logger = logging.getLogger(__name__)


@router.message(F.content_type == ContentType.PHOTO)
async def handle_photo(message: types.Message, state: FSMContext) -> None:
    """Handle all photo messages and process them based on state"""
    current_state = await state.get_state()
    logger.info('Handling photo message from user %s in state %s', message.from_user.id, current_state)

    if not message.photo:
        await message.reply('Пожалуйста, отправьте фотографию.')
        return

    # Get the largest photo
    photo = message.photo[-1]

    # Import bot here to avoid circular import
    from src.bot import bot

    # Download photo from Telegram
    file_info = await bot.get_file(photo.file_id)
    if file_info.file_path is None:
        await message.reply('Ошибка при получении фотографии. Пожалуйста, попробуйте еще раз.')
        return

    file_bytes = await bot.download_file(file_info.file_path)
    if file_bytes is None:
        await message.reply('Ошибка при скачивании фотографии. Пожалуйста, попробуйте еще раз.')
        return

    # Upload photo to MinIO
    file_name = f'profile_photo_{message.from_user.id}.jpg'
    minio_path = upload_file(message.from_user.id, file_name, file_bytes.read())

    # Get MinIO URL for the photo
    photo_url = get_file_path(minio_path)

    # Check if we're in registration state
    if current_state == AuthGroup.registration_photo.state:
        # Get all collected data
        user_data = await state.get_data()
        logger.info('Creating user with data: %s', user_data)

        # Create user and profile
        user = UserCreate(
            user_id=message.from_user.id,
            username=message.from_user.username or f'user_{message.from_user.id}',
            first_name=user_data['first_name'],
            age=user_data['age'],
            gender=user_data['gender'],
            city_name=user_data['city_name'],
            bio=user_data['bio'],
            photo_url=photo_url,
        )

        profile = ProfileCreate(
            user_id=message.from_user.id,
            bio=user_data['bio'],
            photo_url=photo_url,
            preferred_gender=user_data.get('preferred_gender'),
            preferred_age_min=user_data.get('preferred_age_min'),
            preferred_age_max=user_data.get('preferred_age_max'),
        )

        # Send data to RabbitMQ for processing
        async with channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange('user_files', ExchangeType.TOPIC, durable=True)

            registration_message = RegistrationMessage(
                user=user, profile=profile, correlation_id=context.get(HeaderKeys.correlation_id)
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
                    body=msgpack.packb(registration_message.model_dump()),
                    content_type='application/x-msgpack',
                    headers={'correlation_id': context.get(HeaderKeys.correlation_id)},
                ),
                routing_key='user_messages',
            )

        TOTAL_SEND_MESSAGES.labels(operation='registration').inc()

        # Clear state and send success message
        await state.clear()
        await message.reply('Спасибо за регистрацию!')
    else:
        # If not in registration state, inform user
        await message.reply('Пожалуйста, используйте команды для взаимодействия с ботом.')
