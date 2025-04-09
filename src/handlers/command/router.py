from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import ContentType

from src.logger import logger

from .file import check_state, initiate_upload, show_files
from .start import help_command, start

router = Router()

# Регистрируем обработчики команд и текстовых сообщений
router.message.register(start, Command('start'))
router.message.register(initiate_upload, Command('upload'))
router.message.register(show_files, Command('show_files'))
router.message.register(check_state, Command('check_state'))
router.message.register(help_command, Command('help'))


# Обработчик для текстовых сообщений, которые не обрабатываются другими
@router.message(lambda message: message.content_type == ContentType.TEXT)
async def echo(message: types.Message) -> None:
    logger.warning('Необработанное текстовое сообщение.')
    await message.answer('Пожалуйста, отправьте корректный запрос.')
