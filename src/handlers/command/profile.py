from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
import aiohttp
import os
import tempfile

from src.handlers.states.profile import ProfileGroup
from src.schema.user import UserInDB
from src.schema.profile import ProfileInDB
from src.services.user import get_user_by_id, update_user
from src.services.profile import get_profile_by_user_id, update_profile
from src.services.city import get_city_by_id
from config.settings import settings

router = Router()
logger = logging.getLogger(__name__)


async def download_from_presigned_url(url: str) -> str | None:
    """Download file from presigned URL and return local path."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    content = await resp.read()
                    # Create a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                        f.write(content)
                        return f.name
    except Exception as e:
        logger.error('Error downloading file from URL: %s', e)
        return None


@router.message(Command('profile'))
async def handle_profile_command(message: Message, state: FSMContext) -> None:
    """Handle the /profile command to display user's profile."""
    user = await get_user_by_id(message.from_user.id)
    profile = await get_profile_by_user_id(message.from_user.id)

    if not user or not profile:
        await message.answer('Please complete your registration first using /start')
        return

    await state.set_state(ProfileGroup.viewing)
    await display_profile(message, user, profile)


async def display_profile(message: Message, user: UserInDB, profile: ProfileInDB) -> None:
    """Display user's profile with edit buttons."""
    city = await get_city_by_id(user.city_id) if user.city_id else None

    text = (
        f'👤 <b>Your Profile</b>\n\n'
        f'📝 <b>Name:</b> {user.first_name}\n'
        f'🎂 <b>Age:</b> {user.age}\n'
        f'👫 <b>Gender:</b> {user.gender}\n'
        f'📍 <b>City:</b> {city.name if city else "Not set"}\n'
        f'📖 <b>Bio:</b> {profile.bio or "Not set"}\n\n'
        f'💝 <b>Preferences</b>\n'
        f'👫 <b>Preferred Gender:</b> {profile.preferred_gender or "Not set"}\n'
        f'🎂 <b>Preferred Age Range:</b> {profile.preferred_age_min}-'
        f'{profile.preferred_age_max if profile.preferred_age_max else "∞"}\n'
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='✏️ Edit Profile', callback_data='edit_profile')
    keyboard.button(text='🔄 Refresh', callback_data='refresh_profile')

    if profile.photo_url:
        try:
            # Download the photo from the presigned URL
            async with aiohttp.ClientSession() as session:
                async with session.get(profile.photo_url) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        # Create a temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as f:
                            f.write(content)
                            local_path = f.name

                        # Send photo with caption
                        await message.answer_photo(
                            photo=FSInputFile(local_path), caption=text, reply_markup=keyboard.as_markup()
                        )

                        # Clean up the temporary file
                        try:
                            os.unlink(local_path)
                        except Exception as e:
                            logger.error('Error deleting temporary file: %s', e)
                    else:
                        logger.error('Failed to download photo from URL: status %s', resp.status)
                        await message.answer('Error loading profile photo.')
                        await message.answer(text=text, reply_markup=keyboard.as_markup())
        except Exception as e:
            logger.error('Error loading profile photo: %s', e)
            await message.answer('Error loading profile photo. Displaying profile without photo.')
            await message.answer(text=text, reply_markup=keyboard.as_markup())
    else:
        await message.answer(text=text, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == 'edit_profile')
async def handle_edit_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle the edit profile button click."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text='Имя', callback_data='edit_name')
    keyboard.button(text='Возраст', callback_data='edit_age')
    keyboard.button(text='Город', callback_data='edit_city')
    keyboard.button(text='О себе', callback_data='edit_bio')
    keyboard.button(text='Фото', callback_data='edit_photo')
    keyboard.button(text='Пол', callback_data='edit_gender')
    keyboard.button(text='Предпочитаемый пол', callback_data='edit_preferred_gender')
    keyboard.adjust(2)

    # Check if the message has text content
    if callback.message and callback.message.text:
        await callback.message.edit_text('Что вы хотите изменить в профиле?', reply_markup=keyboard.as_markup())
    else:
        # If the message doesn't have text (e.g., it's a photo), send a new message
        await callback.message.answer('Что вы хотите изменить в профиле?', reply_markup=keyboard.as_markup())

    await state.set_state(ProfileGroup.editing)


@router.callback_query(F.data == 'back_to_profile')
async def handle_back_to_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle the back button click to return to profile view."""
    user = await get_user_by_id(callback.from_user.id)
    profile = await get_profile_by_user_id(callback.from_user.id)

    if not user or not profile:
        await callback.message.answer('Please complete your registration first using /start')
        return

    await state.set_state(ProfileGroup.viewing)
    await display_profile(callback.message, user, profile)


@router.callback_query(F.data == 'refresh_profile')
async def handle_refresh_profile(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle the refresh button click to update profile view."""
    user = await get_user_by_id(callback.from_user.id)
    profile = await get_profile_by_user_id(callback.from_user.id)

    if not user or not profile:
        await callback.message.answer('Please complete your registration first using /start')
        return

    await state.set_state(ProfileGroup.viewing)
    await display_profile(callback.message, user, profile)


@router.callback_query(F.data == 'edit_name')
async def handle_edit_name(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle the edit name button click."""
    if callback.message:
        await callback.message.edit_text('Please enter your new name:')
    await state.set_state(ProfileGroup.editing_name)


@router.message(ProfileGroup.editing_name)
async def handle_name_input(message: Message, state: FSMContext) -> None:
    """Handle the name input."""
    user = await get_user_by_id(message.from_user.id)
    if not user:
        await message.answer('Please complete your registration first using /start')
        return

    await update_user(user.user_id, first_name=message.text)
    await message.answer('Name updated successfully!')
    await state.set_state(ProfileGroup.viewing)
    await display_profile(message, user, await get_profile_by_user_id(user.user_id))


@router.callback_query(F.data == 'edit_age')
async def handle_edit_age(callback: CallbackQuery, state: FSMContext) -> None:
    """Handle the edit age button click."""
    if callback.message:
        await callback.message.edit_text('Please enter your new age:')
    await state.set_state(ProfileGroup.editing_age)


@router.message(ProfileGroup.editing_age)
async def handle_age_input(message: Message, state: FSMContext) -> None:
    """Handle the age input."""
    try:
        age = int(message.text)
        if age < 18 or age > 100:
            await message.answer('Please enter a valid age between 18 and 100')
            return
    except ValueError:
        await message.answer('Please enter a valid number')
        return

    user = await get_user_by_id(message.from_user.id)
    if not user:
        await message.answer('Please complete your registration first using /start')
        return

    await update_user(user.user_id, age=age)
    await message.answer('Age updated successfully!')
    await state.set_state(ProfileGroup.viewing)
    await display_profile(message, user, await get_profile_by_user_id(user.user_id))
