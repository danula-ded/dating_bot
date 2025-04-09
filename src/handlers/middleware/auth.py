from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import TelegramObject

from src.handlers.states.auth import AuthGroup


class AuthMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        current_state = await data['state'].get_state()
        if not current_state or current_state == AuthGroup.no_authorized:
            raise SkipHandler('Unauthorized')

        return await handler(event, data)
