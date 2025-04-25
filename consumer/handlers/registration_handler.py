from typing import Dict, Any
from src.model.user import User
from src.storage.user_storage import UserStorage


class RegistrationHandler:
    def __init__(self, user_storage: UserStorage):
        self.user_storage = user_storage

    async def handle(self, message: Dict[str, Any]) -> None:
        """
        Handle user registration event from the queue

        Args:
            message: Dictionary containing registration data
                    Expected keys:
                    - user_id: int
                    - username: str
                    - first_name: str
                    - last_name: str
                    - phone: str
        """
        try:
            user = User(
                user_id=message['user_id'],
                username=message['username'],
                first_name=message['first_name'],
                last_name=message['last_name'],
                phone=message['phone'],
            )

            await self.user_storage.create_user(user)

        except Exception as e:
            # Log the error and potentially retry the operation
            print(f"Error processing registration: {str(e)}")
            raise
