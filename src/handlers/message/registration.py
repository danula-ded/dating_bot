import logging

import aio_pika
import msgpack
from aio_pika import ExchangeType
from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ContentType, Message
from starlette_context import context
from starlette_context.header_keys import HeaderKeys

from src.handlers.states.auth import AuthGroup
from src.metrics import TOTAL_SEND_MESSAGES
from src.schema.registration import RegistrationMessage
from src.schema.user import UserCreate
from src.storage.minio_client import get_file_path, upload_file
from src.storage.rabbit import channel_pool

logger = logging.getLogger(__name__)
router = Router()


@router.message(AuthGroup.registration_name)
@router.message(AuthGroup.registration_age)
@router.message(AuthGroup.registration_gender)
@router.message(AuthGroup.registration_city)
@router.message(AuthGroup.registration_bio)
async def handle_registration(message: types.Message, state: FSMContext) -> None:
    """Unified handler for registration states"""
    current_state = await state.get_state()
    logger.info('Handling registration state %s for user %s', current_state, message.from_user.id)

    if not message.text:
        await message.reply('Пожалуйста, введите текст.')
        return

    if current_state == AuthGroup.registration_name.state:
        name = message.text.strip()
        if not name:
            await message.reply('Пожалуйста, введите ваше имя текстом.')
            return
        await state.update_data(first_name=name)
        await state.set_state(AuthGroup.registration_age)
        await message.reply('Отлично! Теперь введите ваш возраст (только число):')

    elif current_state == AuthGroup.registration_age.state:
        if not message.text.isdigit():
            await message.reply('Пожалуйста, введите возраст числом.')
            return
        age = int(message.text)
        if age < 18:
            await message.reply('Извините, но вы должны быть старше 18 лет.')
            return
        await state.update_data(age=age)
        await state.set_state(AuthGroup.registration_gender)
        await message.reply('Выберите ваш пол:\n1. Мужской\n2. Женский\n3. Другой\nВведите номер варианта:')

    elif current_state == AuthGroup.registration_gender.state:
        gender_map = {'1': 'male', '2': 'female', '3': 'other'}
        if message.text not in gender_map:
            await message.reply('Пожалуйста, выберите вариант 1, 2 или 3.')
            return
        await state.update_data(gender=gender_map[message.text])
        await state.set_state(AuthGroup.registration_city)
        await message.reply('Введите название вашего города:')

    elif current_state == AuthGroup.registration_city.state:
        await state.update_data(city=message.text)
        await state.set_state(AuthGroup.registration_bio)
        await message.reply('Расскажите немного о себе (краткое описание):')

    elif current_state == AuthGroup.registration_bio.state:
        await state.update_data(bio=message.text)
        await state.set_state(AuthGroup.registration_photo)
        await message.reply('Отправьте свою фотографию для профиля:')


@router.message(AuthGroup.registration_photo, F.content_type == ContentType.PHOTO)
async def handle_photo(message: types.Message, state: FSMContext) -> None:
    """Handle profile photo upload"""
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

    # Get all collected data
    user_data = await state.get_data()

    # Create user and profile
    user = UserCreate(
        telegram_id=message.from_user.id,
        first_name=user_data['first_name'],
        age=user_data['age'],
        gender=user_data['gender'],
        city=user_data['city'],
        bio=user_data['bio'],
        photo_url=photo_url,
    )

    # Send data to RabbitMQ for processing
    async with channel_pool.acquire() as channel:
        exchange = await channel.declare_exchange('user_files', ExchangeType.TOPIC, durable=True)

        message = RegistrationMessage(user=user, correlation_id=context.get(HeaderKeys.correlation_id))

        await exchange.publish(
            aio_pika.Message(
                body=msgpack.packb(message.model_dump()),
                content_type='application/x-msgpack',
                headers={'correlation_id': context.get(HeaderKeys.correlation_id)},
            ),
            routing_key='user_messages',
        )

    TOTAL_SEND_MESSAGES.inc()

    # Clear state and send success message
    await state.clear()
    await message.reply('Спасибо за регистрацию! Ваш профиль будет доступен после проверки модератором.')
