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

        # Разрешаем все сообщения в процессе регистрации
        if current_state and (
            current_state == AuthGroup.registration_name.state
            or current_state == AuthGroup.registration_age.state
            or current_state == AuthGroup.registration_gender.state
            or current_state == AuthGroup.registration_city.state
            or current_state == AuthGroup.registration_bio.state
            or current_state == AuthGroup.registration_photo.state
        ):
            return await handler(event, data)

        # Пропускаем только если состояние не установлено или равно no_authorized
        if not current_state or current_state == AuthGroup.no_authorized.state:
            raise SkipHandler('Unauthorized')

        return await handler(event, data)
