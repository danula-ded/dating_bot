from aiogram.fsm.state import State, StatesGroup


class ProfileGroup(StatesGroup):
    viewing = State()
    editing = State()
    editing_name = State()
    editing_age = State()
    editing_gender = State()
    editing_city = State()
    editing_bio = State()
    editing_photo = State()
    editing_preferred_gender = State()
    editing_preferred_age_min = State()
    editing_preferred_age_max = State()
