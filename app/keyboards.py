from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_tasks

inline_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Мои задачи', callback_data='my_task')],
    [InlineKeyboardButton(text='Контакты', callback_data='contact')],
    [InlineKeyboardButton(text='Обратная связь', callback_data='feedback')],
    [InlineKeyboardButton(text='Запрос нейросети', callback_data='ai_req')],
])

get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить номер',
                                                           request_contact=True)]],
                                 resize_keyboard=True)

# Клавиатура для возврата в главное меню
back_to_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start")],
        [KeyboardButton(text="Мои задачи")]
    ],
    resize_keyboard=True
)

# Клавиатура для отмены запроса к нейросети
ai_cancel = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Отменить', callback_data='back')]
    ]
)

# Клавиатура после ответа нейросети
after_ai_response = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start")],
        [KeyboardButton(text="Мои задачи")]
    ],
    resize_keyboard=True
)

back_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back')]
    ]
)




async def my_task_kb(tg_id):
    tasks = await get_tasks(tg_id)
    keyboard = InlineKeyboardBuilder()

    keyboard.row(InlineKeyboardButton(text='Добавить задачу', callback_data='add'))

    if tasks:
        keyboard.row(
            InlineKeyboardButton(text='Удалить', callback_data='delete'),
            InlineKeyboardButton(text='Изменить', callback_data='change'),
            InlineKeyboardButton(text='⏰ Напоминания', callback_data='remind'),
            width=2
        )

    keyboard.row(InlineKeyboardButton(text='Назад', callback_data='back'))
    return keyboard.as_markup()


async def delete_tasks(tg_id):
    tasks = await get_tasks(tg_id)
    keyboard = InlineKeyboardBuilder()
    for task in tasks:
        keyboard.add(InlineKeyboardButton(
            text=f"❌ {task.task}",
            callback_data=f'delete_{task.id}'))
    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))  # Добавлено
    return keyboard.as_markup()


async def edit_tasks(tg_id):
    tasks = await get_tasks(tg_id)
    keyboard = InlineKeyboardBuilder()
    for task in tasks:
        keyboard.add(InlineKeyboardButton(
            text=f"✏️ {task.task}",
            callback_data=f'edit_{task.id}'))
    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))  # Добавлено
    return keyboard.as_markup()


async def remind_tasks(tg_id):
    tasks = await get_tasks(tg_id)
    keyboard = InlineKeyboardBuilder()
    for task in tasks:
        keyboard.add(InlineKeyboardButton(
            text=f"⏰ {task.task[:15]}...",
            callback_data=f'remind_{task.id}'
        ))
    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    return keyboard.as_markup()


confirm_reminder = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Да", callback_data="remind_yes"),
            InlineKeyboardButton(text="Нет", callback_data="remind_no")
        ]
    ]
)