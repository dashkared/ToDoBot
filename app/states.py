from aiogram.fsm.state import StatesGroup, State

class Newsletter(StatesGroup):
    message = State()

class Gen(StatesGroup):
    wait = State()
    conversation = State()

class TaskActions(StatesGroup):
    adding = State()
    deleting = State()
    changing = State()
    new_text = State()
    setting_reminder = State()
    reminder_time = State()
    ask_reminder = State()
    edit_reminder = State()