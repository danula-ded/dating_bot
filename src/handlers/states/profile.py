from aiogram.fsm.state import State, StatesGroup


class ProfileGroup(StatesGroup):
    viewing = State()  # Viewing profile
    editing = State()  # Choosing what to edit
    editing_name = State()  # Editing name
    editing_age = State()  # Editing age
    editing_gender = State()  # Editing gender
    editing_city = State()  # Editing city
    editing_bio = State()  # Editing bio
    editing_photo = State()  # Editing photo
    editing_preferred_gender = State()  # Editing preferred gender
    editing_preferred_age_min = State()  # Editing minimum preferred age
    editing_preferred_age_max = State()  # Editing maximum preferred age
