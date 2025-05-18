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
                                 resize_keyboard=True,
                                 persistent=True)

# Клавиатура для возврата в главное меню
back_to_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Главное меню"), KeyboardButton(text="Мои задачи")]
    ],
    resize_keyboard=True,
    persistent=True
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
        [KeyboardButton(text="Главное меню"), KeyboardButton(text="Мои задачи")]
    ],
    resize_keyboard=True,
    persistent=True
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
            InlineKeyboardButton(text='Удалить', callback_data='delete_0'),
            InlineKeyboardButton(text='Изменить', callback_data='change_0'),
            InlineKeyboardButton(text='⏰ Напоминания', callback_data='remind_0'),
            width=2
        )

    keyboard.row(InlineKeyboardButton(text='Назад', callback_data='back'))
    return keyboard.as_markup()


TASKS_PER_PAGE = 5


async def delete_tasks(tg_id, page=0):
    tasks = await get_tasks(tg_id)
    keyboard = InlineKeyboardBuilder()

    # Calculate the slice of tasks for the current page
    start_idx = page * TASKS_PER_PAGE
    end_idx = start_idx + TASKS_PER_PAGE
    paginated_tasks = tasks[start_idx:end_idx]

    # Add each task on its own row
    for task in paginated_tasks:
        keyboard.row(InlineKeyboardButton(
            text=f"❌ {task.task}",
            callback_data=f'delete_{task.id}'))

    # Calculate total pages
    total_pages = (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE

    # Add navigation buttons on the last row
    keyboard.row(
        InlineKeyboardButton(
            text="⬅️",
            callback_data=f"delete_prev_{page}"),
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages if total_pages > 0 else 1}",
            callback_data="noop"),  # No-op button for display only
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"delete_next_{page}" if end_idx < len(tasks) else "noop")
    )

    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    return keyboard.as_markup()


async def edit_tasks(tg_id, page=0):
    tasks = await get_tasks(tg_id)
    keyboard = InlineKeyboardBuilder()

    # Calculate the slice of tasks for the current page
    start_idx = page * TASKS_PER_PAGE
    end_idx = start_idx + TASKS_PER_PAGE
    paginated_tasks = tasks[start_idx:end_idx]

    # Add each task on its own row
    for task in paginated_tasks:
        keyboard.row(InlineKeyboardButton(
            text=f"✏️ {task.task}",
            callback_data=f'edit_{task.id}'))

    # Calculate total pages
    total_pages = (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE

    # Add navigation buttons on the last row
    keyboard.row(
        InlineKeyboardButton(
            text="⬅️",
            callback_data=f"change_prev_{page}"),
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages if total_pages > 0 else 1}",
            callback_data="noop"),
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"change_next_{page}" if end_idx < len(tasks) else "noop")
    )

    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back"))
    return keyboard.as_markup()


async def remind_tasks(tg_id, page=0):
    tasks = await get_tasks(tg_id)
    keyboard = InlineKeyboardBuilder()

    # Calculate the slice of tasks for the current page
    start_idx = page * TASKS_PER_PAGE
    end_idx = start_idx + TASKS_PER_PAGE
    paginated_tasks = tasks[start_idx:end_idx]

    # Add each task on its own row
    for task in paginated_tasks:
        keyboard.row(InlineKeyboardButton(
            text=f"⏰ {task.task}",
            callback_data=f'remind_{task.id}'
        ))

    # Calculate total pages
    total_pages = (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE

    # Add navigation buttons on the last row
    keyboard.row(
        InlineKeyboardButton(
            text="⬅️",
            callback_data=f"remind_prev_{page}"),
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages if total_pages > 0 else 1}",
            callback_data="noop"),
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"remind_next_{page}" if end_idx < len(tasks) else "noop")
    )

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