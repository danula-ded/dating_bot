from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.storage.redis import get_next_profile
from src.api.producer import send_profile_request, send_interaction_event
from src.logger import logger

router = Router()


@router.message(Command('search'))
async def handle_search_command(message: Message, state: FSMContext):
    """Handle the /search command to find profiles."""
    user_id = message.from_user.id
    logger.info('Search command received from user %s', user_id)
    
    try:
        # Get next profile from Redis
        profile = await get_next_profile(user_id)
        logger.info('Retrieved next profile from Redis for user %s: %s', user_id, profile)
        
        if not profile:
            # No profiles in Redis, request more from the queue
            logger.info('No profiles in Redis for user %s, requesting more', user_id)
            await send_profile_request(user_id, action='search')
            await message.answer('Searching for profiles for you. Please try again in a moment.')
            return
        
        # Create keyboard with like/dislike buttons
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text='❤️ Like', callback_data=f'like_{profile["user_id"]}')
        keyboard.button(text='👎 Dislike', callback_data=f'dislike_{profile["user_id"]}')
        keyboard.adjust(2)
        
        # Display profile with photo if available
        if profile.get('photo_url'):
            await message.answer_photo(
                photo=profile['photo_url'],
                caption=format_profile_text(profile),
                reply_markup=keyboard.as_markup()
            )
        else:
            await message.answer(
                text=format_profile_text(profile),
                reply_markup=keyboard.as_markup()
            )
        
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
        
        # Request new profiles after like
        await send_profile_request(user_id, action='search')
        logger.info('Profile update request sent after like for user %s', user_id)
        
        # Get next profile from Redis
        profile = await get_next_profile(user_id)
        logger.info('Retrieved next profile after like for user %s: %s', user_id, profile)
        
        if not profile:
            await callback.message.edit_text('❤️ You liked this profile! Searching for more profiles...')
        else:
            # Create keyboard for next profile
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text='❤️ Like', callback_data=f'like_{profile["user_id"]}')
            keyboard.button(text='👎 Dislike', callback_data=f'dislike_{profile["user_id"]}')
            keyboard.adjust(2)
            
            # Update message with next profile
            if profile.get('photo_url'):
                await callback.message.edit_media(
                    media=InputMediaPhoto(
                        media=profile['photo_url'],
                        caption=format_profile_text(profile)
                    ),
                    reply_markup=keyboard.as_markup()
                )
            else:
                await callback.message.edit_text(
                    text=format_profile_text(profile),
                    reply_markup=keyboard.as_markup()
                )
        
        await callback.answer('❤️ Profile liked!')
    except Exception as e:
        logger.error('Error in handle_like: %s', str(e))
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
        
        # Request new profiles after dislike
        await send_profile_request(user_id, action='search')
        logger.info('Profile update request sent after dislike for user %s', user_id)
        
        # Get next profile from Redis
        profile = await get_next_profile(user_id)
        logger.info('Retrieved next profile after dislike for user %s: %s', user_id, profile)
        
        if not profile:
            # If there's no next profile, send a new message instead of editing
            await callback.message.answer('👎 You disliked this profile! Searching for more profiles...')
            await callback.answer('👎 Profile disliked!')
            return
        
        # Create keyboard for next profile
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text='❤️ Like', callback_data=f'like_{profile["user_id"]}')
        keyboard.button(text='👎 Dislike', callback_data=f'dislike_{profile["user_id"]}')
        keyboard.adjust(2)
        
        # Update message with next profile
        if profile.get('photo_url'):
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=profile['photo_url'],
                    caption=format_profile_text(profile)
                ),
                reply_markup=keyboard.as_markup()
            )
        else:
            await callback.message.edit_text(
                text=format_profile_text(profile),
                reply_markup=keyboard.as_markup()
            )
        
        await callback.answer('👎 Profile disliked!')
    except Exception as e:
        logger.error('Error in handle_dislike: %s', str(e))
        await callback.answer('Произошла ошибка при обработке дизлайка')


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