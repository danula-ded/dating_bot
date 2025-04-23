from consumer.model.profile import Profile
from consumer.storage import db


async def update_profile(profile: Profile) -> None:
    """Update profile in database."""
    await db.profiles.update_one(
        {'_id': profile.id},
        {'$set': profile.model_dump(exclude={'id'})}
    ) 