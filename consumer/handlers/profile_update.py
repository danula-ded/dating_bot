from consumer.services.user import update_user
from consumer.services.profile import update_profile
from consumer.model.user import User
from consumer.model.profile import Profile
from consumer.logger import logger


async def handle_profile_update(message: dict):
    """Handle profile update messages from the queue."""
    try:
        user_id = message['user_id']
        field = message['field']
        value = message['value']
        username = message.get('username')  # Get username from message

        if field in ['first_name', 'age', 'gender', 'city_id', 'username']:
            # Update user fields
            user = await User.get(user_id)
            if not user:
                logger.error('User %s not found', user_id)
                return

            setattr(user, field, value)
            if username:  # If username is provided, update it
                user.username = username
            await update_user(user)
            logger.info('Updated user %s field %s to %s', user_id, field, value)

        elif field in ['bio', 'photo_url', 'preferred_gender']:
            # Update profile fields
            profile = await Profile.get(user_id)
            if not profile:
                logger.error('Profile for user %s not found', user_id)
                return

            setattr(profile, field, value)
            await update_profile(profile)
            logger.info('Updated profile %s field %s to %s', user_id, field, value)

        elif field == 'preferred_age_range':
            # Update preferred age range
            profile = await Profile.get(user_id)
            if not profile:
                logger.error('Profile for user %s not found', user_id)
                return

            profile.preferred_age_min = value['min']
            profile.preferred_age_max = value['max']
            await update_profile(profile)
            logger.info('Updated profile %s preferred age range to %s', user_id, value)

        else:
            logger.error('Unknown field %s for user %s', field, user_id)

    except Exception as e:
        logger.error('Error processing profile update: %s', str(e))
        raise 