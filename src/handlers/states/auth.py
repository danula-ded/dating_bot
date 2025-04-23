from aiogram.fsm.state import State, StatesGroup


class AuthGroup(StatesGroup):
    no_authorized = State()
    registration = State()
    registration_name = State()
    registration_age = State()
    registration_gender = State()
    registration_city = State()
    registration_bio = State()
    registration_preferred_gender = State()
    registration_preferred_age_min = State()
    registration_preferred_age_max = State()
    registration_photo = State()
    authorized = State()
