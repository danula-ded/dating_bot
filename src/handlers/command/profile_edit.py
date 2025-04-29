import aio_pika
import msgpack
from aio_pika import ExchangeType
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from starlette_context import context
from starlette_context.header_keys import HeaderKeys

from src.handlers.states.profile import ProfileGroup
from src.schema.user import UserUpdate
from src.services.user import get_user_by_id
from src.services.profile import get_profile_by_user_id
from src.storage.minio_client import check_minio_connection, get_file_path
from src.storage.rabbit import channel_pool
from src.metrics import TOTAL_SEND_MESSAGES
from src.logger import logger

router = Router()


@router.message(Command('profile_edit'))
async def profile_edit(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await get_user_by_id(user_id)
    if not user:
        await message.answer('Пожалуйста, сначала зарегистрируйтесь с помощью команды /start')
        return

    profile = await get_profile_by_user_id(user_id)
    if not profile:
        await message.answer('Профиль не найден. Пожалуйста, сначала создайте профиль с помощью команды /start')
        return

    builder = InlineKeyboardBuilder()
    builder.button(text='Имя', callback_data='edit_name')
    builder.button(text='Возраст', callback_data='edit_age')
    builder.button(text='Город', callback_data='edit_city')
    builder.button(text='О себе', callback_data='edit_bio')
    builder.button(text='Фото', callback_data='edit_photo')
    builder.button(text='Пол', callback_data='edit_gender')
    builder.button(text='Предпочитаемый пол', callback_data='edit_preferred_gender')
    builder.adjust(2)

    await message.answer('Что вы хотите изменить в профиле?', reply_markup=builder.as_markup())


@router.callback_query(F.data == "edit_name")
async def handle_edit_name(callback: CallbackQuery, state: FSMContext):
    """Handle editing name."""
    await callback.message.edit_text("Please enter your new name:")
    await state.set_state(ProfileGroup.editing_name)


@router.callback_query(F.data == "edit_age")
async def handle_edit_age(callback: CallbackQuery, state: FSMContext):
    """Handle editing age."""
    await callback.message.edit_text("Please enter your new age (must be 18 or older):")
    await state.set_state(ProfileGroup.editing_age)


@router.callback_query(F.data == "edit_gender")
async def handle_edit_gender(callback: CallbackQuery, state: FSMContext):
    """Handle editing gender."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="👨 Male", callback_data="set_gender_male")
    keyboard.button(text="👩 Female", callback_data="set_gender_female")
    keyboard.button(text="⚧ Other", callback_data="set_gender_other")
    keyboard.button(text="🔙 Back", callback_data="back_to_edit")
    keyboard.adjust(2)
    await callback.message.edit_text("Please select your gender:", reply_markup=keyboard.as_markup())
    await state.set_state(ProfileGroup.editing_gender)


@router.callback_query(F.data == "edit_city")
async def handle_edit_city(callback: CallbackQuery, state: FSMContext):
    """Handle editing city."""
    await callback.message.edit_text("Please enter your city name:")
    await state.set_state(ProfileGroup.editing_city)


@router.callback_query(F.data == "edit_bio")
async def handle_edit_bio(callback: CallbackQuery, state: FSMContext):
    """Handle editing bio."""
    await callback.message.edit_text("Please enter your new bio:")
    await state.set_state(ProfileGroup.editing_bio)


@router.callback_query(F.data == "edit_photo")
async def handle_edit_photo(callback: CallbackQuery, state: FSMContext):
    """Handle editing photo."""
    await callback.message.edit_text("Please send your new profile photo:")
    await state.set_state(ProfileGroup.editing_photo)


@router.callback_query(F.data == "edit_preferences")
async def handle_edit_preferences(callback: CallbackQuery, state: FSMContext):
    """Handle editing preferences."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="👫 Preferred Gender", callback_data="edit_preferred_gender")
    keyboard.button(text="🎯 Age Range", callback_data="edit_preferred_age")
    keyboard.button(text="🔙 Back", callback_data="back_to_edit")
    keyboard.adjust(2)
    await callback.message.edit_text("What preferences would you like to edit?", reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "edit_preferred_gender")
async def handle_edit_preferred_gender(callback: CallbackQuery, state: FSMContext):
    """Handle editing preferred gender."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="👨 Male", callback_data="set_preferred_gender_male")
    keyboard.button(text="👩 Female", callback_data="set_preferred_gender_female")
    keyboard.button(text="⚧ Other", callback_data="set_preferred_gender_other")
    keyboard.button(text="🔙 Back", callback_data="back_to_preferences")
    keyboard.adjust(2)
    await callback.message.edit_text("Please select your preferred gender:", reply_markup=keyboard.as_markup())
    await state.set_state(ProfileGroup.editing_preferred_gender)


@router.callback_query(F.data == "edit_preferred_age")
async def handle_edit_preferred_age(callback: CallbackQuery, state: FSMContext):
    """Handle editing preferred age range."""
    await callback.message.edit_text("Please enter the minimum age you'd like to match with (must be 18 or older):")
    await state.set_state(ProfileGroup.editing_preferred_age_min)


@router.message(ProfileGroup.editing_name)
async def process_name_edit(message: Message, state: FSMContext):
    """Process name edit."""
    name = message.text.strip()
    if not name:
        await message.reply("Please enter a valid name.")
        return

    try:
        async with channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange('user_updates', ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue('user_updates', durable=True)
            await queue.bind(exchange, 'user_updates')

            update = UserUpdate(first_name=name)
            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb(
                        {'user_id': message.from_user.id, 'update': update.model_dump(), 'field': 'first_name'}
                    ),
                    correlation_id=context.get(HeaderKeys.correlation_id),
                ),
                routing_key='user_updates',
            )
            TOTAL_SEND_MESSAGES.labels(operation='update_user').inc()

        await message.reply("Your name has been updated!")
        await handle_edit_profile_command(message, state)
    except Exception as e:
        logger.error("Error updating name: %s", e)
        await message.reply("An error occurred while updating your name. Please try again.")


@router.message(ProfileGroup.editing_age)
async def process_age_edit(message: Message, state: FSMContext):
    """Process age edit."""
    if not message.text.isdigit():
        await message.reply("Please enter a valid age (numbers only).")
        return

    age = int(message.text)
    if age < 18:
        await message.reply("You must be 18 or older.")
        return

    try:
        async with channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange('user_updates', ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue('user_updates', durable=True)
            await queue.bind(exchange, 'user_updates')

            update = UserUpdate(age=age)
            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb({'user_id': message.from_user.id, 'update': update.model_dump(), 'field': 'age'}),
                    correlation_id=context.get(HeaderKeys.correlation_id),
                ),
                routing_key='user_updates',
            )
            TOTAL_SEND_MESSAGES.labels(operation='update_user').inc()

        await message.reply("Your age has been updated!")
        await handle_edit_profile_command(message, state)
    except Exception as e:
        logger.error("Error updating age: %s", e)
        await message.reply("An error occurred while updating your age. Please try again.")


@router.callback_query(F.data.startswith("set_gender_"))
async def process_gender_edit(callback: CallbackQuery, state: FSMContext):
    """Process gender edit."""
    gender = callback.data.replace("set_gender_", "")

    try:
        async with channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange('user_updates', ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue('user_updates', durable=True)
            await queue.bind(exchange, 'user_updates')

            update = UserUpdate(gender=gender)
            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb({'user_id': callback.from_user.id, 'update': update.model_dump(), 'field': 'gender'}),
                    correlation_id=context.get(HeaderKeys.correlation_id),
                ),
                routing_key='user_updates',
            )
            TOTAL_SEND_MESSAGES.labels(operation='update_user').inc()

        await callback.message.edit_text("Your gender has been updated!")
        await handle_edit_profile_command(callback.message, state)
    except Exception as e:
        logger.error("Error updating gender: %s", e)
        await callback.message.edit_text("An error occurred while updating your gender. Please try again.")


@router.message(ProfileGroup.editing_city)
async def process_city_edit(message: Message, state: FSMContext):
    """Process city edit."""
    city_name = message.text.strip()
    if not city_name:
        await message.reply("Please enter a valid city name.")
        return

    try:
        async with channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange('user_updates', ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue('user_updates', durable=True)
            await queue.bind(exchange, 'user_updates')

            update = UserUpdate(city_name=city_name)
            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb(
                        {'user_id': message.from_user.id, 'update': update.model_dump(), 'field': 'city_name'}
                    ),
                    correlation_id=context.get(HeaderKeys.correlation_id),
                ),
                routing_key='user_updates',
            )
            TOTAL_SEND_MESSAGES.labels(operation='update_user').inc()

        await message.reply("Your city has been updated!")
        await handle_edit_profile_command(message, state)
    except Exception as e:
        logger.error("Error updating city: %s", e)
        await message.reply("An error occurred while updating your city. Please try again.")


@router.message(ProfileGroup.editing_bio)
async def process_bio_edit(message: Message, state: FSMContext):
    """Process bio edit."""
    bio = message.text.strip()
    if not bio:
        await message.reply("Please enter a valid bio.")
        return

    try:
        async with channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange('user_updates', ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue('user_updates', durable=True)
            await queue.bind(exchange, 'user_updates')

            update = UserUpdate(bio=bio)
            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb({'user_id': message.from_user.id, 'update': update.model_dump(), 'field': 'bio'}),
                    correlation_id=context.get(HeaderKeys.correlation_id),
                ),
                routing_key='user_updates',
            )
            TOTAL_SEND_MESSAGES.labels(operation='update_user').inc()

        await message.reply("Your bio has been updated!")
        await handle_edit_profile_command(message, state)
    except Exception as e:
        logger.error("Error updating bio: %s", e)
        await message.reply("An error occurred while updating your bio. Please try again.")


@router.message(ProfileGroup.editing_photo, F.content_type.in_({'photo', 'document'}))
async def process_photo_edit(message: Message, state: FSMContext):
    """Process photo edit."""
    if not await check_minio_connection():
        await message.reply("Error: Storage service is unavailable. Please try again later.")
        return

    try:
        if message.content_type == 'photo':
            photo = message.photo[-1]
            file_path = await get_file_path(photo.file_id)
        else:
            document = message.document
            if not document.mime_type.startswith('image/'):
                await message.reply("Please send an image file.")
                return
            file_path = await get_file_path(document.file_id)

        if not file_path:
            await message.reply("Error: Could not process the image. Please try again.")
            return

        async with channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange('user_updates', ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue('user_updates', durable=True)
            await queue.bind(exchange, 'user_updates')

            update = UserUpdate(photo_url=file_path)
            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb(
                        {'user_id': message.from_user.id, 'update': update.model_dump(), 'field': 'photo_url'}
                    ),
                    correlation_id=context.get(HeaderKeys.correlation_id),
                ),
                routing_key='user_updates',
            )
            TOTAL_SEND_MESSAGES.labels(operation='update_user').inc()

        await message.reply("Your photo has been updated!")
        await handle_edit_profile_command(message, state)
    except Exception as e:
        logger.error("Error updating photo: %s", e)
        await message.reply("An error occurred while updating your photo. Please try again.")


@router.callback_query(F.data.startswith("set_preferred_gender_"))
async def process_preferred_gender_edit(callback: CallbackQuery, state: FSMContext):
    """Process preferred gender edit."""
    gender = callback.data.replace("set_preferred_gender_", "")

    try:
        async with channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange('user_updates', ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue('user_updates', durable=True)
            await queue.bind(exchange, 'user_updates')

            update = UserUpdate(preferred_gender=gender)
            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb(
                        {'user_id': callback.from_user.id, 'update': update.model_dump(), 'field': 'preferred_gender'}
                    ),
                    correlation_id=context.get(HeaderKeys.correlation_id),
                ),
                routing_key='user_updates',
            )
            TOTAL_SEND_MESSAGES.labels(operation='update_user').inc()

        await callback.message.edit_text("Your preferred gender has been updated!")
        await handle_edit_profile_command(callback.message, state)
    except Exception as e:
        logger.error("Error updating preferred gender: %s", e)
        await callback.message.edit_text("An error occurred while updating your preferred gender. Please try again.")


@router.message(ProfileGroup.editing_preferred_age_min)
async def process_preferred_age_min_edit(message: Message, state: FSMContext):
    """Process preferred minimum age edit."""
    if not message.text.isdigit():
        await message.reply("Please enter a valid age (numbers only).")
        return

    age = int(message.text)
    if age < 18:
        await message.reply("Minimum age must be 18 or older.")
        return

    await state.update_data(preferred_age_min=age)
    await message.reply("Please enter the maximum age you'd like to match with:")
    await state.set_state(ProfileGroup.editing_preferred_age_max)


@router.message(ProfileGroup.editing_preferred_age_max)
async def process_preferred_age_max_edit(message: Message, state: FSMContext):
    """Process preferred maximum age edit."""
    if not message.text.isdigit():
        await message.reply("Please enter a valid age (numbers only).")
        return

    age = int(message.text)
    if age < 18:
        await message.reply("Maximum age must be 18 or older.")
        return

    data = await state.get_data()
    min_age = data.get('preferred_age_min', 18)

    if age < min_age:
        await message.reply("Maximum age must be greater than or equal to minimum age.")
        return

    try:
        async with channel_pool.acquire() as channel:
            exchange = await channel.declare_exchange('user_updates', ExchangeType.TOPIC, durable=True)
            queue = await channel.declare_queue('user_updates', durable=True)
            await queue.bind(exchange, 'user_updates')

            update = UserUpdate(preferred_age_min=min_age, preferred_age_max=age)
            await exchange.publish(
                aio_pika.Message(
                    msgpack.packb(
                        {'user_id': message.from_user.id, 'update': update.model_dump(), 'field': 'preferred_age_range'}
                    ),
                    correlation_id=context.get(HeaderKeys.correlation_id),
                ),
                routing_key='user_updates',
            )
            TOTAL_SEND_MESSAGES.labels(operation='update_user').inc()

        await message.reply("Your preferred age range has been updated!")
        await handle_edit_profile_command(message, state)
    except Exception as e:
        logger.error("Error updating preferred age range: %s", e)
        await message.reply("An error occurred while updating your preferred age range. Please try again.")
