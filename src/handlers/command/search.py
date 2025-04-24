from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.storage.redis import get_user_profiles, get_redis
from src.api.producer import send_profile_request, send_interaction_event
from src.logger import logger

router = Router()


@router.message(Command('search'))
async def handle_search_command(message: Message, state: FSMContext):
    """Handle the /search command to find profiles."""
    user_id = message.from_user.id
    logger.info('Search command received from user %s', user_id)
    
    try:
        # Get profiles from Redis
        profiles = await get_user_profiles(user_id)
        logger.info('Retrieved profiles from Redis for user %s: %s', user_id, profiles)
        
        if not profiles:
            # No profiles in Redis, request more from the queue
            logger.info('No profiles in Redis for user %s, requesting more', user_id)
            await send_profile_request(user_id, action='search')
            await message.answer('Searching for profiles for you. Please try again in a moment.')
            return
        
        # Get the first profile from the list
        profile = profiles[0]
        logger.info('Displaying profile for user %s: %s', user_id, profile)
        
        # Remove the profile from the list
        profiles.pop(0)
        
        # Update Redis with remaining profiles
        redis = await get_redis()
        key = f'user:{user_id}:profiles'
        
        if profiles:
            # If there are still profiles, update Redis
            logger.info('Updating Redis with remaining profiles for user %s: %s', user_id, profiles)
            await redis.set(key, str(profiles))
        else:
            # If no profiles left, delete the key and request more
            logger.info('No profiles left for user %s, requesting more', user_id)
            await redis.delete(key)
            await send_profile_request(user_id, action='search')
        
        # Create keyboard with like/dislike buttons
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text='❤️ Like', callback_data=f'like_{profile["user_id"]}')
        keyboard.button(text='👎 Dislike', callback_data=f'dislike_{profile["user_id"]}')
        keyboard.button(text='🔙 Back to Profile', callback_data='back_to_profile')
        keyboard.adjust(2, 1)
        
        # Display profile
        text = (
            f'👤 <b>Profile</b>\n\n'
            f'📝 <b>Name:</b> {profile["first_name"]}\n'
            f'🎂 <b>Age:</b> {profile["age"]}\n'
            f'👫 <b>Gender:</b> {profile["gender"]}\n'
        )
        
        if profile.get('bio'):
            text += f'📖 <b>Bio:</b> {profile["bio"]}\n'
        
        await message.answer(text, reply_markup=keyboard.as_markup())
        
    except Exception as e:
        logger.error('Error in search command for user %s: %s', user_id, str(e))
        await message.answer('An error occurred while searching for profiles. Please try again later.')


@router.callback_query(F.data.startswith('like_'))
async def handle_like(callback: CallbackQuery, state: FSMContext):
    """Handle the like button click."""
    target_user_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    logger.info('Like action received from user %s for target user %s', user_id, target_user_id)
    
    # Send like event to common queue
    await send_interaction_event(user_id, target_user_id, 'like')
    logger.info('Like event sent to queue for user %s -> target %s', user_id, target_user_id)
    
    # Get next profile from Redis
    profiles = await get_user_profiles(user_id)
    logger.info('Retrieved profiles after like for user %s: %s', user_id, profiles)
    
    if not profiles:
        # If no profiles left, request more
        logger.info('No profiles left after like for user %s, requesting more', user_id)
        await send_profile_request(user_id, action='search')
        await callback.message.edit_text('❤️ You liked this profile! Searching for more profiles...')
    else:
        # Show next profile
        profile = profiles[0]
        profiles.pop(0)
        logger.info('Displaying next profile after like for user %s: %s', user_id, profile)
        
        # Update Redis
        redis = await get_redis()
        key = f'user:{user_id}:profiles'
        if profiles:
            logger.info('Updating Redis with remaining profiles after like for user %s: %s', user_id, profiles)
            await redis.set(key, str(profiles))
        else:
            logger.info('No profiles left after like for user %s, requesting more', user_id)
            await redis.delete(key)
            await send_profile_request(user_id, action='search')
        
        # Create keyboard for next profile
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text='❤️ Like', callback_data=f'like_{profile["user_id"]}')
        keyboard.button(text='👎 Dislike', callback_data=f'dislike_{profile["user_id"]}')
        keyboard.button(text='🔙 Back to Profile', callback_data='back_to_profile')
        keyboard.adjust(2, 1)
        
        # Display next profile
        text = (
            f'👤 <b>Profile</b>\n\n'
            f'📝 <b>Name:</b> {profile["first_name"]}\n'
            f'🎂 <b>Age:</b> {profile["age"]}\n'
            f'👫 <b>Gender:</b> {profile["gender"]}\n'
        )
        
        if profile.get('bio'):
            text += f'📖 <b>Bio:</b> {profile["bio"]}\n'
        
        await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
        
    try:
        await callback.answer()
    except Exception as e:
        logger.error('Error answering callback for like action: %s', str(e))


@router.callback_query(F.data.startswith('dislike_'))
async def handle_dislike(callback: CallbackQuery, state: FSMContext):
    """Handle the dislike button click."""
    target_user_id = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    logger.info('Dislike action received from user %s for target user %s', user_id, target_user_id)
    
    # Send dislike event to common queue
    await send_interaction_event(user_id, target_user_id, 'dislike')
    logger.info('Dislike event sent to queue for user %s -> target %s', user_id, target_user_id)
    
    # Get next profile from Redis
    profiles = await get_user_profiles(user_id)
    logger.info('Retrieved profiles after dislike for user %s: %s', user_id, profiles)
    
    if not profiles:
        # If no profiles left, request more
        logger.info('No profiles left after dislike for user %s, requesting more', user_id)
        await send_profile_request(user_id, action='search')
        await callback.message.edit_text('👎 You disliked this profile! Searching for more profiles...')
    else:
        # Show next profile
        profile = profiles[0]
        profiles.pop(0)
        logger.info('Displaying next profile after dislike for user %s: %s', user_id, profile)
        
        # Update Redis
        redis = await get_redis()
        key = f'user:{user_id}:profiles'
        if profiles:
            logger.info('Updating Redis with remaining profiles after dislike for user %s: %s', user_id, profiles)
            await redis.set(key, str(profiles))
        else:
            logger.info('No profiles left after dislike for user %s, requesting more', user_id)
            await redis.delete(key)
            await send_profile_request(user_id, action='search')
        
        # Create keyboard for next profile
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text='❤️ Like', callback_data=f'like_{profile["user_id"]}')
        keyboard.button(text='👎 Dislike', callback_data=f'dislike_{profile["user_id"]}')
        keyboard.button(text='🔙 Back to Profile', callback_data='back_to_profile')
        keyboard.adjust(2, 1)
        
        # Display next profile
        text = (
            f'👤 <b>Profile</b>\n\n'
            f'📝 <b>Name:</b> {profile["first_name"]}\n'
            f'🎂 <b>Age:</b> {profile["age"]}\n'
            f'👫 <b>Gender:</b> {profile["gender"]}\n'
        )
        
        if profile.get('bio'):
            text += f'📖 <b>Bio:</b> {profile["bio"]}\n'
        
        await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
        
    try:
        await callback.answer()
    except Exception as e:
        logger.error('Error answering callback for dislike action: %s', str(e)) 