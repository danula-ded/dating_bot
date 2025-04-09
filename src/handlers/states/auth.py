from aiogram.fsm.state import State, StatesGroup


class AuthGroup(StatesGroup):
    no_authorized = State()
    authorized = State()
