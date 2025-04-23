from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from src.handlers.middleware.auth import AuthMiddleware
from src.handlers.states.auth import AuthGroup
from src.logger import logger

router = Router()
router.message.middleware(AuthMiddleware())


@router.message(F.text)
async def handle_text_message(message: types.Message, state: FSMContext) -> None:
    """Обработчик текстовых сообщений"""
    current_state = await state.get_state()
    logger.info('Handling text message from user %s in state %s', message.from_user.id, current_state)

    if not current_state:
        logger.warning('Необработанное текстовое сообщение.')
        await message.reply('Пожалуйста, используйте команды для взаимодействия с ботом.')
        return

    if current_state == AuthGroup.registration_name.state:
        name = message.text.strip()
        if not name:
            await message.reply('Пожалуйста, введите ваше имя текстом.')
            return
        await state.update_data(first_name=name)
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
        await state.set_state(AuthGroup.registration_gender)
        await message.reply('Выберите ваш пол:\n1. Мужской\n2. Женский\n3. Другой\nВведите номер варианта:')

    elif current_state == AuthGroup.registration_gender.state:
        gender_map = {'1': 'male', '2': 'female', '3': 'other'}
        if message.text not in gender_map:
            await message.reply('Пожалуйста, выберите вариант 1, 2 или 3.')
            return
        await state.update_data(gender=gender_map[message.text])
        await state.set_state(AuthGroup.registration_city)
        await message.reply('Введите название вашего города:')

    elif current_state == AuthGroup.registration_city.state:
        await state.update_data(city_name=message.text)
        await state.set_state(AuthGroup.registration_bio)
        await message.reply('Расскажите немного о себе (краткое описание):')

    elif current_state == AuthGroup.registration_bio.state:
        await state.update_data(bio=message.text)
        await state.set_state(AuthGroup.registration_preferred_gender)
        await message.reply(
            'Выберите предпочитаемый пол для знакомств:\n1. Мужской\n2. Женский\n3. Другой\nВведите номер варианта:'
        )

    elif current_state == AuthGroup.registration_preferred_gender.state:
        gender_map = {'1': 'male', '2': 'female', '3': 'other'}
        if message.text not in gender_map:
            await message.reply('Пожалуйста, выберите вариант 1, 2 или 3.')
            return
        await state.update_data(preferred_gender=gender_map[message.text])
        await state.set_state(AuthGroup.registration_preferred_age_min)
        await message.reply('Введите минимальный предпочитаемый возраст (только число):')

    elif current_state == AuthGroup.registration_preferred_age_min.state:
        if not message.text.isdigit():
            await message.reply('Пожалуйста, введите возраст числом.')
            return
        age_min = int(message.text)
        if age_min < 18:
            await message.reply('Минимальный возраст должен быть не менее 18 лет.')
            return
        await state.update_data(preferred_age_min=age_min)
        await state.set_state(AuthGroup.registration_preferred_age_max)
        await message.reply('Введите максимальный предпочитаемый возраст (только число):')

    elif current_state == AuthGroup.registration_preferred_age_max.state:
        if not message.text.isdigit():
            await message.reply('Пожалуйста, введите возраст числом.')
            return
        age_max = int(message.text)
        user_data = await state.get_data()
        age_min = user_data.get('preferred_age_min', 18)
        
        if age_max < age_min:
            await message.reply(f'Максимальный возраст должен быть не меньше минимального ({age_min}).')
            return
        
        await state.update_data(preferred_age_max=age_max)
        await state.set_state(AuthGroup.registration_photo)
        await message.reply('Отправьте свою фотографию для профиля:')

    else:
        logger.warning('Необработанное текстовое сообщение в состоянии %s', current_state)
        await message.reply('Пожалуйста, используйте команды для взаимодействия с ботом.')
