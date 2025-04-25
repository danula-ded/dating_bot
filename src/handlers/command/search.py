from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.storage.redis import get_next_profile, get_user_profiles
from src.api.producer import send_profile_request, send_interaction_event
from src.logger import logger

router = Router()


async def check_profiles_in_redis(user_id: int) -> bool:
    """
    Check if there are profiles available in Redis for the user.

    Args:
        user_id: The ID of the user

    Returns:
        bool: True if profiles exist, False otherwise
    """
    try:
        profiles = await get_user_profiles(user_id)
        return profiles is not None and len(profiles) > 0
    except Exception as e:
        logger.error('Error checking profiles in Redis for user %s: %s', user_id, str(e))
        return False


@router.message(Command('search'))
async def handle_search_command(message: Message, state: FSMContext):
    """Handle the /search command to find profiles."""
    user_id = message.from_user.id
    logger.info('Search command received from user %s', user_id)

    try:
        # Check if there are profiles in Redis
        has_profiles = await check_profiles_in_redis(user_id)
        if not has_profiles:
            # No profiles in Redis, request more from the queue
            logger.info('No profiles in Redis for user %s, requesting more', user_id)
            await send_profile_request(user_id, action='search')

            # Create keyboard with refresh button
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text='🔄 Обновить', callback_data='refresh_profiles')
            keyboard.adjust(1)

            # Show "please wait" message with refresh button
            await message.answer(
                'Профили загружаются, пожалуйста, подождите...\n\n'
                'Нажмите кнопку "Обновить", чтобы проверить наличие новых профилей.',
                reply_markup=keyboard.as_markup(),
            )
            return

        # Get next profile from Redis
        profile = await get_next_profile(user_id)
        logger.info('Retrieved next profile from Redis for user %s: %s', user_id, profile)

        if not profile:
            # This should not happen if check_profiles_in_redis returned True
            logger.error('No profile returned from Redis for user %s despite check passing', user_id)
            await message.answer('Произошла ошибка при загрузке профиля. Пожалуйста, попробуйте позже.')
            return

        # Create keyboard with like/dislike buttons
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text='❤️ Like', callback_data=f'like_{profile["user_id"]}')
        keyboard.button(text='👎 Dislike', callback_data=f'dislike_{profile["user_id"]}')
        keyboard.adjust(2)

        # Display profile with photo if available
        if profile.get('photo_url'):
            await message.answer_photo(
                photo=profile['photo_url'], caption=format_profile_text(profile), reply_markup=keyboard.as_markup()
            )
        else:
            await message.answer(text=format_profile_text(profile), reply_markup=keyboard.as_markup())

    except Exception as e:
        logger.error('Error in search command for user %s: %s', user_id, str(e))
        await message.answer('An error occurred while searching for profiles. Please try again later.')


@router.callback_query(F.data.startswith('like_'))
async def handle_like(callback: CallbackQuery, state: FSMContext):
    """Handle the like button click."""
    target_user_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    logger.info('Like action received from user %s for target user %s', user_id, target_user_id)

    try:
        # Send like event to common queue
        await send_interaction_event(user_id, target_user_id, 'like')
        logger.info('Like event sent to queue for user %s -> target %s', user_id, target_user_id)

        # Get next profile from Redis
        profile = await get_next_profile(user_id)
        logger.info('Retrieved next profile after like for user %s: %s', user_id, profile)

        if not profile:
            # Create keyboard with refresh button
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text='🔄 Обновить', callback_data='refresh_profiles')
            keyboard.adjust(1)

            # Show "please wait" message with refresh button
            await callback.message.edit_text(
                '❤️ Вы поставили лайк! Профили загружаются, пожалуйста, подождите...\n\n'
                'Нажмите кнопку "Обновить", чтобы проверить наличие новых профилей.',
                reply_markup=keyboard.as_markup(),
            )

            # Request new profiles from the queue only when Redis is empty
            await send_profile_request(user_id, action='search')
            logger.info('Profile update request sent for user %s after empty profiles', user_id)
        else:
            # Create keyboard for next profile
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text='❤️ Like', callback_data=f'like_{profile["user_id"]}')
            keyboard.button(text='👎 Dislike', callback_data=f'dislike_{profile["user_id"]}')
            keyboard.adjust(2)

            # Update message with next profile
            if profile.get('photo_url'):
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=profile['photo_url'], caption=format_profile_text(profile)),
                    reply_markup=keyboard.as_markup(),
                )
            else:
                await callback.message.edit_text(text=format_profile_text(profile), reply_markup=keyboard.as_markup())

        await callback.answer('❤️ Profile liked!')
    except Exception as e:
        logger.error('Error in handle_like: %s', str(e))
        # В случае ошибки показываем сообщение о завершении подборки
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text='🔄 Обновить', callback_data='refresh_profiles')
        keyboard.adjust(1)

        try:
            await callback.message.edit_text(
                '❤️ Вы поставили лайк! Подборка профилей завершена.\n\n'
                'Нажмите кнопку "Обновить", чтобы проверить наличие новых профилей.',
                reply_markup=keyboard.as_markup(),
            )
        except Exception as edit_error:
            logger.error('Error editing message after exception: %s', str(edit_error))
            await callback.answer('Произошла ошибка при обработке лайка')


@router.callback_query(F.data.startswith('dislike_'))
async def handle_dislike(callback: CallbackQuery, state: FSMContext):
    """Handle the dislike button click."""
    target_user_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    logger.info('Dislike action received from user %s for target user %s', user_id, target_user_id)

    try:
        # Send dislike event to common queue
        await send_interaction_event(user_id, target_user_id, 'dislike')
        logger.info('Dislike event sent to queue for user %s -> target %s', user_id, target_user_id)

        # Get next profile from Redis
        profile = await get_next_profile(user_id)
        logger.info('Retrieved next profile after dislike for user %s: %s', user_id, profile)

        if not profile:
            # Create keyboard with refresh button
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text='🔄 Обновить', callback_data='refresh_profiles')
            keyboard.adjust(1)

            # Show "please wait" message with refresh button
            await callback.message.edit_text(
                '👎 Вы поставили дизлайк! Профили загружаются, пожалуйста, подождите...\n\n'
                'Нажмите кнопку "Обновить", чтобы проверить наличие новых профилей.',
                reply_markup=keyboard.as_markup(),
            )

            # Request new profiles from the queue only when Redis is empty
            await send_profile_request(user_id, action='search')
            logger.info('Profile update request sent for user %s after empty profiles', user_id)
        else:
            # Create keyboard for next profile
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text='❤️ Like', callback_data=f'like_{profile["user_id"]}')
            keyboard.button(text='👎 Dislike', callback_data=f'dislike_{profile["user_id"]}')
            keyboard.adjust(2)

            # Update message with next profile
            if profile.get('photo_url'):
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=profile['photo_url'], caption=format_profile_text(profile)),
                    reply_markup=keyboard.as_markup(),
                )
            else:
                await callback.message.edit_text(text=format_profile_text(profile), reply_markup=keyboard.as_markup())

        await callback.answer('👎 Profile disliked!')
    except Exception as e:
        logger.error('Error in handle_dislike: %s', str(e))
        # В случае ошибки показываем сообщение о завершении подборки
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text='🔄 Обновить', callback_data='refresh_profiles')
        keyboard.adjust(1)

        try:
            await callback.message.edit_text(
                '👎 Вы поставили дизлайк! Подборка профилей завершена.\n\n'
                'Нажмите кнопку "Обновить", чтобы проверить наличие новых профилей.',
                reply_markup=keyboard.as_markup(),
            )
        except Exception as edit_error:
            logger.error('Error editing message after exception: %s', str(edit_error))
            await callback.answer('Произошла ошибка при обработке дизлайка')


@router.callback_query(F.data == 'refresh_profiles')
async def handle_refresh_profiles(callback: CallbackQuery, state: FSMContext):
    """Handle the refresh profiles button click."""
    user_id = callback.from_user.id
    logger.info('Refresh profiles request received from user %s', user_id)

    try:
        # Request new profiles from the queue
        await send_profile_request(user_id, action='search')
        logger.info('Profile update request sent for user %s', user_id)

        # Get next profile from Redis
        profile = await get_next_profile(user_id)
        logger.info('Retrieved next profile after refresh for user %s: %s', user_id, profile)

        if not profile:
            # Create keyboard with refresh button
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text='🔄 Обновить', callback_data='refresh_profiles')
            keyboard.adjust(1)

            # Show "please wait" message with refresh button
            await callback.message.edit_text(
                'Профили загружаются, пожалуйста, подождите...\n\n'
                'Нажмите кнопку "Обновить", чтобы проверить наличие новых профилей.',
                reply_markup=keyboard.as_markup(),
            )
        elif isinstance(profile, dict) and profile.get('last_profile'):
            # This was the last profile in the selection
            # Create keyboard with refresh button
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text='🔄 Обновить', callback_data='refresh_profiles')
            keyboard.adjust(1)

            # Show "last profile" message with refresh button
            await callback.message.edit_text(
                'Это был последний профиль в подборке.\n\n'
                'Нажмите кнопку "Обновить", чтобы проверить наличие новых профилей.',
                reply_markup=keyboard.as_markup(),
            )
        else:
            # Create keyboard for next profile
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text='❤️ Like', callback_data=f'like_{profile["user_id"]}')
            keyboard.button(text='👎 Dislike', callback_data=f'dislike_{profile["user_id"]}')
            keyboard.adjust(2)

            # Update message with next profile
            if profile.get('photo_url'):
                await callback.message.edit_media(
                    media=InputMediaPhoto(media=profile['photo_url'], caption=format_profile_text(profile)),
                    reply_markup=keyboard.as_markup(),
                )
            else:
                await callback.message.edit_text(text=format_profile_text(profile), reply_markup=keyboard.as_markup())

        await callback.answer('🔄 Профили обновляются...')
    except Exception as e:
        logger.error('Error in handle_refresh_profiles: %s', str(e))
        # В случае ошибки показываем сообщение о завершении подборки
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text='🔄 Обновить', callback_data='refresh_profiles')
        keyboard.adjust(1)

        try:
            await callback.message.edit_text(
                'Произошла ошибка при обновлении профилей.\n\n' 'Нажмите кнопку "Обновить", чтобы попробовать снова.',
                reply_markup=keyboard.as_markup(),
            )
        except Exception as edit_error:
            logger.error('Error editing message after exception: %s', str(edit_error))
            await callback.answer('Произошла ошибка при обновлении профилей')


def format_profile_text(profile: dict) -> str:
    """Format profile information into a readable text."""
    text = (
        f'👤 <b>Profile</b>\n\n'
        f'📝 <b>Name:</b> {profile["first_name"]}\n'
        f'🎂 <b>Age:</b> {profile["age"]}\n'
        f'👫 <b>Gender:</b> {profile["gender"]}\n'
    )

    if profile.get('bio'):
        text += f'📖 <b>Bio:</b> {profile["bio"]}\n'

    if profile.get('interests'):
        text += f'🎯 <b>Interests:</b> {", ".join(profile["interests"])}\n'

    return text
