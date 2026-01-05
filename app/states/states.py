from aiogram.fsm.state import StatesGroup, State


class Registration(StatesGroup):
    age = State()
    height = State()
    weight = State()
    goal = State()
    yourself_or_ai = State()
    kbju = State()

    gender = State()
    activity = State()
    description = State()


class UpdateProfile(StatesGroup):
    new_kbju = State()
    new_height = State()
    new_weight = State()
    new_goal = State()


class EditProfile(StatesGroup):
    object = State()


class DescForProduct(StatesGroup):
    desc = State()
