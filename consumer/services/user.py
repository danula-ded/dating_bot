from consumer.model.user import User
from consumer.storage import db


async def update_user(user: User) -> None:
    """Update user in database."""
    await db.users.update_one(
        {'_id': user.id},
        {'$set': user.model_dump(exclude={'id'})}
    ) 