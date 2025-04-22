from aiogram import Router
from aiogram.filters import Command

from .diagnostic import check_services, debug_info
from .file import check_state, initiate_upload, show_files
from .start import help_command, start

router = Router()

# Регистрируем обработчики команд и текстовых сообщений
router.message.register(start, Command('start'))
router.message.register(initiate_upload, Command('upload'))
router.message.register(show_files, Command('show_files'))
router.message.register(check_state, Command('check_state'))
router.message.register(check_services, Command('check_services'))
router.message.register(debug_info, Command('debug'))
router.message.register(help_command, Command('help'))
