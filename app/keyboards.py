from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_tasks


inline_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Мои задачи', callback_data='my_task')],
    [InlineKeyboardButton(text='Контакты', callback_data='contact')],
    [InlineKeyboardButton(text='Обратная связь', callback_data='feedback')]
])

my_task = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить задачу', callback_data='add')],
    [InlineKeyboardButton(text='Удалить задачу', callback_data='delete'),
     InlineKeyboardButton(text='Изменить задачу', callback_data='change')],
    [InlineKeyboardButton(text='🔄 Обновить список', callback_data='my_task')],
    [InlineKeyboardButton(text='Назад', callback_data='back')]
])

get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить номер',
                                                           request_contact=True)]],
                                 resize_keyboard=True)

async def tasks(tg_id):
    tasks = await get_tasks(tg_id)
    keyboard = InlineKeyboardBuilder()
    for task in tasks:
        keyboard.add(InlineKeyboardButton(
            text=f"📝 {task.task}",
            callback_data=f'task_{task.id}'))
    keyboard.row(InlineKeyboardButton(
        text="⬅️ Назад",
        callback_data='back'))
    return keyboard.as_markup()

async def delete_tasks(tg_id):
    tasks = await get_tasks(tg_id)
    keyboard = InlineKeyboardBuilder()
    for task in tasks:
        keyboard.add(InlineKeyboardButton(
            text=f"❌ {task.task}",
            callback_data=f'delete_{task.id}'))  # Уникальный префикс для удаления
    return keyboard.as_markup()

async def edit_tasks(tg_id):
    tasks = await get_tasks(tg_id)
    keyboard = InlineKeyboardBuilder()
    for task in tasks:
        keyboard.add(InlineKeyboardButton(
            text=f"✏️ {task.task}",
            callback_data=f'edit_{task.id}'))  # Уникальный префикс для изменения
    return keyboard.as_markup()