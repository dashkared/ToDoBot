from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_tasks

'''main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Мои задачи')],
                                     [KeyboardButton(text='Контакты')],
                                     [KeyboardButton(text='Обратная связь')]],
                           resize_keyboard=True,
                           input_field_placeholder= 'Выберите пункт меню...')'''

inline_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Мои задачи', callback_data='my_task')],
    [InlineKeyboardButton(text='Контакты', callback_data='contact')],
    [InlineKeyboardButton(text='Обратная связь', callback_data='feedback')]
])

my_task = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Добавить задачу(-и)', callback_data='add')],
    [InlineKeyboardButton(text='Удалить задачу(-и)', callback_data='delete')],
    [InlineKeyboardButton(text='Изменить задачу(-и)', callback_data='change')],
    [InlineKeyboardButton(text='Назад', callback_data='back')]
])

get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить номер', 
                                                           request_contact=True)]],
                                 resize_keyboard=True)

async def tasks(tg_id):
    tasks = await get_tasks(tg_id)
    keyboard = InlineKeyboardBuilder()
    for task in tasks:
        keyboard.add(InlineKeyboardButton(text=task.task, callback_data=f'task_{task.id}'))
    return keyboard.as_markup()