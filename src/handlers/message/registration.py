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
async def handle_registration_start(message: types.Message, state: FSMContext) -> None:
    """Handle the start of registration process"""
    logger.info('Handling registration start for user %s', message.from_user.id)
    current_state = await state.get_state()
    logger.info('Current state in registration handler: %s', current_state)

    if not message.text or not message.text.strip():
        await message.reply('Пожалуйста, введите ваше имя текстом.')
        return

    await state.update_data(first_name=message.text.strip())
    await state.set_state(AuthGroup.registration_age)
    current_state = await state.get_state()
    logger.info('State after setting registration_age: %s', current_state)
    await message.reply('Отлично! Теперь введите ваш возраст (только число):')


@router.message(AuthGroup.registration_age)
async def handle_age(message: Message, state: FSMContext) -> None:
    """Handle age input"""
    if not message.text or not message.text.isdigit():
        await message.reply('Пожалуйста, введите возраст числом.')
        return

    age = int(message.text)
    if age < 18:
        await message.reply('Извините, но вы должны быть старше 18 лет.')
        return

    await state.update_data(age=age)
    await state.set_state(AuthGroup.registration_gender)
    await message.reply('Выберите ваш пол:\n' '1. Мужской\n' '2. Женский\n' '3. Другой\n' 'Введите номер варианта:')


@router.message(AuthGroup.registration_gender)
async def handle_gender(message: types.Message, state: FSMContext) -> None:
    """Handle gender selection"""
    gender_map = {'1': 'male', '2': 'female', '3': 'other'}

    if not message.text or message.text not in gender_map:
        await message.reply('Пожалуйста, выберите вариант 1, 2 или 3.')
        return

    await state.update_data(gender=gender_map[message.text])
    await state.set_state(AuthGroup.registration_city)
    await message.reply('Введите название вашего города:')


@router.message(AuthGroup.registration_city)
async def handle_city(message: types.Message, state: FSMContext) -> None:
    """Handle city input"""
    if not message.text:
        await message.reply('Пожалуйста, введите название города.')
        return

    await state.update_data(city=message.text)
    await state.set_state(AuthGroup.registration_bio)
    await message.reply('Расскажите немного о себе (краткое описание):')


@router.message(AuthGroup.registration_bio)
async def handle_bio(message: types.Message, state: FSMContext) -> None:
    """Handle bio input"""
    if not message.text:
        await message.reply('Пожалуйста, напишите что-нибудь о себе.')
        return

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
