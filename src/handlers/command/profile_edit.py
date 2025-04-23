from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.handlers.states.profile import ProfileGroup
from src.services.user import get_user_by_id
from src.services.profile import get_profile_by_user_id
from src.services.city import search_cities
from src.handlers.command.profile import display_profile
from src.api.producer import send_profile_update

router = Router()


async def send_update_with_username(message: Message, field: str, value: str):
    """Helper function to send profile update with username."""
    await send_profile_update({
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'field': field,
        'value': value
    })


@router.callback_query(F.data == 'edit_name')
async def handle_edit_name(callback: CallbackQuery, state: FSMContext):
    """Handle the edit name button click."""
    await callback.message.edit_text(
        'Please enter your new name:',
        reply_markup=InlineKeyboardBuilder().button(
            text='🔙 Back', callback_data='back_to_edit'
        ).as_markup()
    )
    await state.set_state(ProfileGroup.editing_name)


@router.message(ProfileGroup.editing_name)
async def handle_name_input(message: Message, state: FSMContext):
    """Handle the new name input."""
    user = await get_user_by_id(message.from_user.id)
    if not user:
        await message.answer('Please complete your registration first using /start')
        return

    # Send update to queue with username
    await send_update_with_username(message, 'first_name', message.text)

    await state.set_state(ProfileGroup.viewing)
    await display_profile(message, user, await get_profile_by_user_id(message.from_user.id))


@router.callback_query(F.data == 'edit_age')
async def handle_edit_age(callback: CallbackQuery, state: FSMContext):
    """Handle the edit age button click."""
    await callback.message.edit_text(
        'Please enter your age (18-100):',
        reply_markup=InlineKeyboardBuilder().button(
            text='🔙 Back', callback_data='back_to_edit'
        ).as_markup()
    )
    await state.set_state(ProfileGroup.editing_age)


@router.message(ProfileGroup.editing_age)
async def handle_age_input(message: Message, state: FSMContext):
    """Handle the new age input."""
    try:
        age = int(message.text)
        if not 18 <= age <= 100:
            await message.answer('Age must be between 18 and 100. Please try again:')
            return

        # Send update to queue with username
        await send_update_with_username(message, 'age', age)

        user = await get_user_by_id(message.from_user.id)
        await state.set_state(ProfileGroup.viewing)
        await display_profile(message, user, await get_profile_by_user_id(message.from_user.id))

    except ValueError:
        await message.answer('Please enter a valid number for age:')


@router.callback_query(F.data == 'edit_gender')
async def handle_edit_gender(callback: CallbackQuery, state: FSMContext):
    """Handle the edit gender button click."""
    builder = InlineKeyboardBuilder()
    builder.button(text='Male', callback_data='gender_male')
    builder.button(text='Female', callback_data='gender_female')
    builder.button(text='Other', callback_data='gender_other')
    builder.button(text='🔙 Back', callback_data='back_to_edit')
    builder.adjust(1)

    await callback.message.edit_text(
        'Please select your gender:',
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProfileGroup.editing_gender)


@router.callback_query(ProfileGroup.editing_gender)
async def handle_gender_selection(callback: CallbackQuery, state: FSMContext):
    """Handle the gender selection."""
    gender = callback.data.split('_')[1]
    
    # Send update to queue with username
    await send_update_with_username(callback.message, 'gender', gender)

    user = await get_user_by_id(callback.from_user.id)
    await state.set_state(ProfileGroup.viewing)
    await display_profile(callback.message, user, await get_profile_by_user_id(callback.from_user.id))


@router.callback_query(F.data == 'edit_city')
async def handle_edit_city(callback: CallbackQuery, state: FSMContext):
    """Handle the edit city button click."""
    await callback.message.edit_text(
        'Please enter your city name:',
        reply_markup=InlineKeyboardBuilder().button(
            text='🔙 Back', callback_data='back_to_edit'
        ).as_markup()
    )
    await state.set_state(ProfileGroup.editing_city)


@router.message(ProfileGroup.editing_city)
async def handle_city_input(message: Message, state: FSMContext):
    """Handle the city name input."""
    cities = await search_cities(message.text)
    if not cities:
        await message.answer('No cities found. Please try again:')
        return

    builder = InlineKeyboardBuilder()
    for city in cities:
        builder.button(
            text=f'{city.name}, {city.country}',
            callback_data=f'city_{city.id}'
        )
    builder.button(text='🔙 Back', callback_data='back_to_edit')
    builder.adjust(1)

    await message.answer(
        'Please select your city:',
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data.startswith('city_'))
async def handle_city_selection(callback: CallbackQuery, state: FSMContext):
    """Handle the city selection."""
    city_id = int(callback.data.split('_')[1])
    
    # Send update to queue with username
    await send_update_with_username(callback.message, 'city_id', city_id)

    user = await get_user_by_id(callback.from_user.id)
    await state.set_state(ProfileGroup.viewing)
    await display_profile(callback.message, user, await get_profile_by_user_id(callback.from_user.id))


@router.callback_query(F.data == 'edit_bio')
async def handle_edit_bio(callback: CallbackQuery, state: FSMContext):
    """Handle the edit bio button click."""
    await callback.message.edit_text(
        'Please enter your bio:',
        reply_markup=InlineKeyboardBuilder().button(
            text='🔙 Back', callback_data='back_to_edit'
        ).as_markup()
    )
    await state.set_state(ProfileGroup.editing_bio)


@router.message(ProfileGroup.editing_bio)
async def handle_bio_input(message: Message, state: FSMContext):
    """Handle the new bio input."""
    # Send update to queue with username
    await send_update_with_username(message, 'bio', message.text)

    user = await get_user_by_id(message.from_user.id)
    await state.set_state(ProfileGroup.viewing)
    await display_profile(message, user, await get_profile_by_user_id(message.from_user.id))


@router.callback_query(F.data == 'edit_photo')
async def handle_edit_photo(callback: CallbackQuery, state: FSMContext):
    """Handle the edit photo button click."""
    await callback.message.edit_text(
        'Please send your new photo:',
        reply_markup=InlineKeyboardBuilder().button(
            text='🔙 Back', callback_data='back_to_edit'
        ).as_markup()
    )
    await state.set_state(ProfileGroup.editing_photo)


@router.message(ProfileGroup.editing_photo, F.photo)
async def handle_photo_input(message: Message, state: FSMContext):
    """Handle the new photo input."""
    # Get the largest photo size
    photo = message.photo[-1]
    
    # Send update to queue with username
    await send_update_with_username(message, 'photo_url', photo.file_id)

    user = await get_user_by_id(message.from_user.id)
    await state.set_state(ProfileGroup.viewing)
    await display_profile(message, user, await get_profile_by_user_id(message.from_user.id))


@router.callback_query(F.data == 'edit_preferences')
async def handle_edit_preferences(callback: CallbackQuery, state: FSMContext):
    """Handle the edit preferences button click."""
    builder = InlineKeyboardBuilder()
    builder.button(text='Preferred Gender', callback_data='edit_preferred_gender')
    builder.button(text='Preferred Age Range', callback_data='edit_preferred_age')
    builder.button(text='🔙 Back', callback_data='back_to_edit')
    builder.adjust(1)

    await callback.message.edit_text(
        'What would you like to edit?',
        reply_markup=builder.as_markup()
    )


@router.callback_query(F.data == 'edit_preferred_gender')
async def handle_edit_preferred_gender(callback: CallbackQuery, state: FSMContext):
    """Handle the edit preferred gender button click."""
    builder = InlineKeyboardBuilder()
    builder.button(text='Male', callback_data='pref_gender_male')
    builder.button(text='Female', callback_data='pref_gender_female')
    builder.button(text='Other', callback_data='pref_gender_other')
    builder.button(text='Any', callback_data='pref_gender_any')
    builder.button(text='🔙 Back', callback_data='back_to_edit')
    builder.adjust(1)

    await callback.message.edit_text(
        'Please select preferred gender:',
        reply_markup=builder.as_markup()
    )
    await state.set_state(ProfileGroup.editing_preferred_gender)


@router.callback_query(ProfileGroup.editing_preferred_gender)
async def handle_preferred_gender_selection(callback: CallbackQuery, state: FSMContext):
    """Handle the preferred gender selection."""
    gender = callback.data.split('_')[2]
    
    # Send update to queue with username
    await send_update_with_username(callback.message, 'preferred_gender', gender)

    user = await get_user_by_id(callback.from_user.id)
    await state.set_state(ProfileGroup.viewing)
    await display_profile(callback.message, user, await get_profile_by_user_id(callback.from_user.id))


@router.callback_query(F.data == 'edit_preferred_age')
async def handle_edit_preferred_age(callback: CallbackQuery, state: FSMContext):
    """Handle the edit preferred age range button click."""
    await callback.message.edit_text(
        'Please enter minimum preferred age (18-100):',
        reply_markup=InlineKeyboardBuilder().button(
            text='🔙 Back', callback_data='back_to_edit'
        ).as_markup()
    )
    await state.set_state(ProfileGroup.editing_preferred_age_min)


@router.message(ProfileGroup.editing_preferred_age_min)
async def handle_preferred_age_min_input(message: Message, state: FSMContext):
    """Handle the minimum preferred age input."""
    try:
        age_min = int(message.text)
        if not 18 <= age_min <= 100:
            await message.answer('Age must be between 18 and 100. Please try again:')
            return

        await state.update_data(preferred_age_min=age_min)
        await message.answer('Now enter maximum preferred age (18-100):')
        await state.set_state(ProfileGroup.editing_preferred_age_max)

    except ValueError:
        await message.answer('Please enter a valid number for age:')


@router.message(ProfileGroup.editing_preferred_age_max)
async def handle_preferred_age_max_input(message: Message, state: FSMContext):
    """Handle the maximum preferred age input."""
    try:
        age_max = int(message.text)
        if not 18 <= age_max <= 100:
            await message.answer('Age must be between 18 and 100. Please try again:')
            return

        data = await state.get_data()
        age_min = data['preferred_age_min']
        
        if age_max < age_min:
            await message.answer('Maximum age must be greater than minimum age. Please try again:')
            return

        # Send update to queue with username
        await send_update_with_username(message, 'preferred_age_range', {
            'min': age_min,
            'max': age_max
        })

        user = await get_user_by_id(message.from_user.id)
        await state.set_state(ProfileGroup.viewing)
        await display_profile(message, user, await get_profile_by_user_id(message.from_user.id))

    except ValueError:
        await message.answer('Please enter a valid number for age:')


@router.callback_query(F.data == 'back_to_edit')
async def handle_back_to_edit(callback: CallbackQuery, state: FSMContext):
    """Handle the back to edit button click."""
    user = await get_user_by_id(callback.from_user.id)
    await state.set_state(ProfileGroup.viewing)
    await display_profile(callback.message, user, await get_profile_by_user_id(callback.from_user.id)) 