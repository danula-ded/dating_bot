from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ContentType
import msgpack
import aio_pika
from aio_pika import ExchangeType
from starlette_context import context
from starlette_context.header_keys import HeaderKeys
from aiogram.filters import Command

from src.handlers.states.auth import AuthGroup
from src.schema.user import UserCreate
from src.schema.profile import ProfileCreate
from src.schema.registration import RegistrationMessage
from src.storage.minio_client import upload_file, get_file_path
from src.storage.rabbit import channel_pool
from src.metrics import TOTAL_SEND_MESSAGES
from src.handlers.message.registration.keyboards import get_registration_keyboard
from src.handlers.message.registration.callbacks import (
    process_name,
    process_city,
    process_bio,
    process_photo,
    process_gender,
    process_interests,
    process_preferred_gender,
    process_preferred_age_min,
    process_preferred_age_max,
)

router = Router()


@router.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "Добро пожаловать в бот знакомств! Давайте начнем регистрацию.",
        reply_markup=get_registration_keyboard()
    )


@router.message(AuthGroup.registration_name)
async def handle_name(message: Message):
    await process_name(message)


@router.message(AuthGroup.registration_age)
async def handle_age(message: Message, state: FSMContext) -> None:
    """Handle age input"""
    if not message.text or not message.text.isdigit():
        await message.reply("Пожалуйста, введите возраст числом.")
        return
        
    age = int(message.text)
    if age < 18:
        await message.reply("Извините, но вы должны быть старше 18 лет.")
        return
        
    await state.update_data(age=age)
    await state.set_state(AuthGroup.registration_gender)
    await message.reply(
        "Выберите ваш пол:\n"
        "1. Мужской\n"
        "2. Женский\n"
        "3. Другой\n"
        "Введите номер варианта:"
    )


@router.message(AuthGroup.registration_gender)
async def handle_gender(message: Message):
    await process_gender(message)


@router.message(AuthGroup.registration_city)
async def handle_city(message: Message):
    await process_city(message)


@router.message(AuthGroup.registration_interests)
async def handle_interests(message: Message):
    await process_interests(message)


@router.message(AuthGroup.registration_photo, F.content_type == ContentType.PHOTO)
async def handle_photo(message: Message):
    await process_photo(message)


@router.message(AuthGroup.registration_bio)
async def handle_bio(message: Message):
    await process_bio(message)


@router.message(AuthGroup.registration_preferred_gender)
async def handle_preferred_gender(message: Message):
    await process_preferred_gender(message)


@router.message(AuthGroup.registration_preferred_age_min)
async def handle_preferred_age_min(message: Message):
    await process_preferred_age_min(message)


@router.message(AuthGroup.registration_preferred_age_max)
async def handle_preferred_age_max(message: Message):
    await process_preferred_age_max(message)


@router.message(AuthGroup.registration)
async def handle_registration_start(message: types.Message, state: FSMContext) -> None:
    """Handle the start of registration process"""
    if not message.text:
        await message.reply("Пожалуйста, введите ваше имя текстом.")
        return
        
    await state.update_data(first_name=message.text)
    await state.set_state(AuthGroup.registration_age)
    await message.reply("Отлично! Теперь введите ваш возраст (только число):")


@router.message(AuthGroup.registration_gender)
async def handle_gender(message: types.Message, state: FSMContext) -> None:
    """Handle gender selection"""
    gender_map = {
        "1": "male",
        "2": "female",
        "3": "other"
    }
    
    if not message.text or message.text not in gender_map:
        await message.reply("Пожалуйста, выберите вариант 1, 2 или 3.")
        return
        
    await state.update_data(gender=gender_map[message.text])
    await state.set_state(AuthGroup.registration_city)
    await message.reply("Введите название вашего города:")


@router.message(AuthGroup.registration_city)
async def handle_city(message: types.Message, state: FSMContext) -> None:
    """Handle city input"""
    if not message.text:
        await message.reply("Пожалуйста, введите название города.")
        return
        
    await state.update_data(city=message.text)
    await state.set_state(AuthGroup.registration_bio)
    await message.reply(
        "Расскажите немного о себе (краткое описание):"
    )


@router.message(AuthGroup.registration_bio)
async def handle_bio(message: types.Message, state: FSMContext) -> None:
    """Handle bio input"""
    if not message.text:
        await message.reply("Пожалуйста, напишите что-нибудь о себе.")
        return
        
    await state.update_data(bio=message.text)
    await state.set_state(AuthGroup.registration_photo)
    await message.reply(
        "Отправьте свою фотографию для профиля:"
    )


@router.message(AuthGroup.registration_photo, F.content_type == ContentType.PHOTO)
async def handle_photo(message: types.Message, state: FSMContext) -> None:
    """Handle profile photo upload"""
    if not message.photo:
        await message.reply("Пожалуйста, отправьте фотографию.")
        return
        
    # Get the largest photo
    photo = message.photo[-1]
    
    # Import bot here to avoid circular import
    from src.bot import bot
    
    # Download photo from Telegram
    file_info = await bot.get_file(photo.file_id)
    if file_info.file_path is None:
        await message.reply("Ошибка при получении фотографии. Пожалуйста, попробуйте еще раз.")
        return
        
    file_bytes = await bot.download_file(file_info.file_path)
    if file_bytes is None:
        await message.reply("Ошибка при скачивании фотографии. Пожалуйста, попробуйте еще раз.")
        return
        
    # Upload photo to MinIO
    file_name = f"profile_photo_{message.from_user.id}.jpg"
    minio_path = upload_file(message.from_user.id, file_name, file_bytes.read())
    
    # Get MinIO URL for the photo
    photo_url = get_file_path(minio_path)
    
    # Get all collected data
    user_data = await state.get_data()
    
    # Create user profile
    user = UserCreate(
        user_id=message.from_user.id,
        first_name=user_data['first_name'],
        age=user_data['age'],
        gender=user_data['gender'],
        city_name=user_data['city']
    )
    
    profile = ProfileCreate(
        user_id=message.from_user.id,
        bio=user_data['bio'],
        photo_url=photo_url
    )
    
    # Create registration message
    registration_message = RegistrationMessage(
        user=user,
        profile=profile
    )
    
    # Send to RabbitMQ
    async with channel_pool.acquire() as channel:
        # Declare exchange and queue
        exchange = await channel.declare_exchange('user_registration', ExchangeType.TOPIC, durable=True)
        queue = await channel.declare_queue('user_registration_queue', durable=True)
        await queue.bind(exchange, 'user_registration')
        
        # Publish message
        await exchange.publish(
            aio_pika.Message(
                msgpack.packb(registration_message.model_dump()),
                correlation_id=context.get(HeaderKeys.correlation_id),
            ),
            routing_key='user_registration',
        )
    
    TOTAL_SEND_MESSAGES.labels(operation='user_registration').inc()
    
    await state.set_state(AuthGroup.authorized)
    await message.reply(
        "Регистрация успешно завершена! 🎉\n"
        "Теперь вы можете использовать все функции бота.\n"
        "Используйте /help для просмотра доступных команд."
    ) 