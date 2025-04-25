from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.handlers.states.profile import ProfileGroup
from src.schema.user import UserInDB
from src.schema.profile import ProfileInDB
from src.services.user import get_user_by_id
from src.services.profile import get_profile_by_user_id
from src.services.city import get_city_by_id

router = Router()


@router.message(Command("profile"))
async def handle_profile_command(message: Message, state: FSMContext):
    """Handle the /profile command to display user's profile."""
    user = await get_user_by_id(message.from_user.id)
    profile = await get_profile_by_user_id(message.from_user.id)

    if not user or not profile:
        await message.answer("Please complete your registration first using /start")
        return

    await state.set_state(ProfileGroup.viewing)
    await display_profile(message, user, profile)


async def display_profile(message: Message, user: UserInDB, profile: ProfileInDB):
    """Display user's profile with edit buttons."""
    city = await get_city_by_id(user.city_id) if user.city_id else None

    text = (
        f"👤 <b>Your Profile</b>\n\n"
        f"📝 <b>Name:</b> {user.first_name}\n"
        f"🎂 <b>Age:</b> {user.age}\n"
        f"👫 <b>Gender:</b> {user.gender}\n"
        f"📍 <b>City:</b> {city.name if city else 'Not set'}\n"
        f"📖 <b>Bio:</b> {profile.bio or 'Not set'}\n\n"
        f"💝 <b>Preferences</b>\n"
        f"👫 <b>Preferred Gender:</b> {profile.preferred_gender or 'Not set'}\n"
        f"🎂 <b>Preferred Age Range:</b> {profile.preferred_age_min}-{profile.preferred_age_max if profile.preferred_age_max else '∞'}\n"
    )

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✏️ Edit Profile", callback_data="edit_profile")

    if profile.photo_url:
        await message.answer_photo(photo=profile.photo_url, caption=text, reply_markup=keyboard.as_markup())
    else:
        await message.answer(text=text, reply_markup=keyboard.as_markup())


@router.callback_query(F.data == "edit_profile")
async def handle_edit_profile(callback: CallbackQuery, state: FSMContext):
    """Handle the edit profile button click."""
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="📝 Name", callback_data="edit_name")
    keyboard.button(text="🎂 Age", callback_data="edit_age")
    keyboard.button(text="👫 Gender", callback_data="edit_gender")
    keyboard.button(text="📍 City", callback_data="edit_city")
    keyboard.button(text="📖 Bio", callback_data="edit_bio")
    keyboard.button(text="📸 Photo", callback_data="edit_photo")
    keyboard.button(text="💝 Preferences", callback_data="edit_preferences")
    keyboard.button(text="🔙 Back", callback_data="back_to_profile")
    keyboard.adjust(2)

    await callback.message.edit_text("What would you like to edit?", reply_markup=keyboard.as_markup())
    await state.set_state(ProfileGroup.editing)


@router.callback_query(F.data == "back_to_profile")
async def handle_back_to_profile(callback: CallbackQuery, state: FSMContext):
    """Handle the back button click to return to profile view."""
    user = await get_user_by_id(callback.from_user.id)
    profile = await get_profile_by_user_id(callback.from_user.id)

    if not user or not profile:
        await callback.message.answer("Please complete your registration first using /start")
        return

    await state.set_state(ProfileGroup.viewing)
    await display_profile(callback.message, user, profile)
