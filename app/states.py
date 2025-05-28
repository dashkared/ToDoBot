from aiogram.fsm.state import StatesGroup, State

class Newsletter(StatesGroup):
    message = State() # Состояние для ввода сообщения рассылки

class Gen(StatesGroup):
    wait = State() # Состояние ожидания запроса к ИИ-ассистенту
    conversation = State() # Состояние активного разговора с ИИ-ассистентом

class TaskActions(StatesGroup):
    adding = State() # Состояние добавления новой задачи
    deleting = State() # Состояние удаления задачи
    changing = State() # Состояние изменения задачи
    new_text = State() # Состояние ввода нового текста задачи
    setting_reminder = State() # Состояние установки напоминания
    reminder_time = State() # Состояние ввода времени напоминания
    ask_reminder = State() # Состояние запроса на установку напоминания
    edit_reminder = State() # Состояние редактирования напоминания