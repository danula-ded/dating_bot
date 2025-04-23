import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from src.handlers.states.auth import AuthGroup
from src.logger import logger

router = Router()


@router.message(AuthGroup.registration_name)
@router.message(AuthGroup.registration_age)
@router.message(AuthGroup.registration_gender)
@router.message(AuthGroup.registration_city)
@router.message(AuthGroup.registration_bio)
async def handle_registration(message: types.Message, state: FSMContext) -> None:
    """Unified handler for registration states"""
    current_state = await state.get_state()
    logger.info('Handling registration state %s for user %s', current_state, message.from_user.id)

    if not message.text:
        await message.reply('Пожалуйста, введите текст.')
        return

    if current_state == AuthGroup.registration_name.state:
        name = message.text.strip()
        if not name:
            await message.reply('Пожалуйста, введите ваше имя текстом.')
            return
        await state.update_data(
            first_name=name,
            username=message.from_user.username or f'user_{message.from_user.id}'
        )
        logger.info('Updated registration data for user %s: %s', message.from_user.id, await state.get_data())
        await state.set_state(AuthGroup.registration_age)
        await message.reply('Отлично! Теперь введите ваш возраст (только число):')

    elif current_state == AuthGroup.registration_age.state:
        if not message.text.isdigit():
            await message.reply('Пожалуйста, введите возраст числом.')
            return
        age = int(message.text)
        if age < 18:
            await message.reply('Извините, но вы должны быть старше 18 лет.')
            return
        await state.update_data(age=age)
        logger.info('Updated registration data for user %s: %s', message.from_user.id, await state.get_data())
        await state.set_state(AuthGroup.registration_gender)
        await message.reply('Выберите ваш пол:\n1. Мужской\n2. Женский\n3. Другой\nВведите номер варианта:')

    elif current_state == AuthGroup.registration_gender.state:
        gender_map = {'1': 'male', '2': 'female', '3': 'other'}
        if message.text not in gender_map:
            await message.reply('Пожалуйста, выберите вариант 1, 2 или 3.')
            return
        await state.update_data(gender=gender_map[message.text])
        logger.info('Updated registration data for user %s: %s', message.from_user.id, await state.get_data())
        await state.set_state(AuthGroup.registration_city)
        await message.reply('Введите название вашего города:')

    elif current_state == AuthGroup.registration_city.state:
        city_name = message.text.strip()
        if not city_name:
            await message.reply('Пожалуйста, введите название города.')
            return
        await state.update_data(city_name=city_name)
        logger.info('Updated registration data for user %s: %s', message.from_user.id, await state.get_data())
        await state.set_state(AuthGroup.registration_bio)
        await message.reply('Расскажите немного о себе (краткое описание):')

    elif current_state == AuthGroup.registration_bio.state:
        await state.update_data(bio=message.text)
        logger.info('Updated registration data for user %s: %s', message.from_user.id, await state.get_data())
        await state.set_state(AuthGroup.registration_photo)
        await message.reply('Отправьте свою фотографию для профиля:')
