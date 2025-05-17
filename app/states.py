from aiogram.fsm.state import StatesGroup, State


class Newsletter(StatesGroup):
    message = State()

class Gen(StatesGroup):
    wait = State()

class TaskActions(StatesGroup):
    adding = State()
    deleting = State()
    changing = State()
    new_text = State()

