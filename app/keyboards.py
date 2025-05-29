from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           InlineKeyboardMarkup, InlineKeyboardButton)
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.database.requests import get_tasks

inline_main = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Мои задачи', callback_data='my_task')],
    [InlineKeyboardButton(text='Мои напоминания', callback_data='view_reminders')],
    [InlineKeyboardButton(text='Контакты', callback_data='contact')],
    [InlineKeyboardButton(text='Обратная связь', callback_data='feedback')],
    [InlineKeyboardButton(text='ИИ-помощник', callback_data='ai_req')],
]) # Создание инлайн-клавиатуры главного меню с кнопками для основных функций бота

get_number = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Отправить номер',
                                                           request_contact=True)]],
                                 resize_keyboard=True,
                                 persistent=True) # Создание клавиатуры с кнопкой для отправки номера телефона пользователя

# Клавиатура для возврата в главное меню
back_to_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Главное меню"), KeyboardButton(text="Мои задачи")]
    ],
    resize_keyboard=True,
    persistent=True
) # Создание клавиатуры с кнопками для возврата в главное меню или просмотра задач

# Клавиатура для отмены запроса к нейросети
ai_cancel = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Отменить', callback_data='back')]
    ]
) # Создание инлайн-клавиатуры с кнопкой для отмены запроса к ИИ-ассистенту

# Клавиатура для разговора с нейросетью
ai_conversation = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Главное меню"), KeyboardButton(text="Мои задачи")],
        [KeyboardButton(text="Новый чат")]
    ],
    resize_keyboard=True,
    persistent=True
) # Создание клавиатуры для взаимодействия с ИИ-ассистентом с кнопками для перехода в меню, задач или начала нового чата

back_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='back')]
    ]
) # Создание инлайн-клавиатуры с кнопкой "Назад" для возврата к предыдущему меню

async def my_task_kb(tg_id):
    tasks = await get_tasks(tg_id) # Получение списка задач пользователя по его Telegram ID
    keyboard = InlineKeyboardBuilder() # Создание строителя инлайн-клавиатуры

    keyboard.row(InlineKeyboardButton(text='Добавить задачу', callback_data='add')) # Добавление кнопки для создания новой задачи

    if tasks: # Проверка наличия задач у пользователя
        keyboard.row(
            InlineKeyboardButton(text='Удалить', callback_data='delete_0'),
            InlineKeyboardButton(text='Изменить', callback_data='change_0')
        ) # Добавление кнопок для удаления и изменения задач, если задачи существуют

    keyboard.row(InlineKeyboardButton(text='Назад', callback_data='back')) # Добавление кнопки "Назад" для возврата
    return keyboard.as_markup() # Возврат готовой инлайн-клавиатуры

TASKS_PER_PAGE = 5 # Константа, определяющая количество задач на одной странице

async def delete_tasks(tg_id, page=0):
    tasks = await get_tasks(tg_id) # Получение списка задач пользователя по его Telegram ID
    keyboard = InlineKeyboardBuilder() # Создание строителя инлайн-клавиатуры

    # Вычисление индексов для текущей страницы
    start_idx = page * TASKS_PER_PAGE # Вычисление начального индекса для текущей страницы
    end_idx = start_idx + TASKS_PER_PAGE # Вычисление конечного индекса для текущей страницы
    paginated_tasks = tasks[start_idx:end_idx] # Получение задач для текущей страницы

    # Добавление списка задач на свою отдельную строку
    for task in paginated_tasks: # Перебор задач на текущей странице
        keyboard.row(InlineKeyboardButton(
            text=f"❌ {task.task}",
            callback_data=f'delete_{task.id}')) # Добавление кнопки для удаления каждой задачи с её ID

    # Вычисление общего количества страниц
    total_pages = (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE # Вычисление количества страниц

    # Добавление кнопок навигации на последнюю строку
    keyboard.row(
        InlineKeyboardButton(
            text="⬅️",
            callback_data=f"delete_prev_{page}"),
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages if total_pages > 0 else 1}",
            callback_data="noop"),  # Кнопка без действия для отображения только номера страницы
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"delete_next_{page}" if end_idx < len(tasks) else "noop")
    ) # Добавление кнопок навигации: назад, номер страницы (без действия), вперёд (если есть следующая страница)

    keyboard.row(InlineKeyboardButton(text="⬅ Назад", callback_data="back")) # Добавление кнопки "Назад" для возврата
    return keyboard.as_markup() # Возврат готовой инлайн-клавиатуры

async def edit_tasks(tg_id, page=0):
    tasks = await get_tasks(tg_id) # Получение списка задач пользователя по его Telegram ID
    keyboard = InlineKeyboardBuilder() # Создание строителя инлайн-клавиатуры

    # Вычисление индексов для текущей страницы
    start_idx = page * TASKS_PER_PAGE # Вычисление начального индекса для текущей страницы
    end_idx = start_idx + TASKS_PER_PAGE # Вычисление конечного индекса для текущей страницы
    paginated_tasks = tasks[start_idx:end_idx] # Получение задач для текущей страницы

    # Добавление списка задач на свою отдельную строку
    for task in paginated_tasks: # Перебор задач на текущей странице
        keyboard.row(InlineKeyboardButton(
            text=f"✏️ {task.task}",
            callback_data=f'change_{task.id}')) # Добавление кнопки для редактирования каждой задачи с её ID

    # Вычисление общего количества страниц
    total_pages = (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE # Вычисление количества страниц

    # Добавление кнопок навигации на последнюю строку
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
    ) # Добавление кнопок навигации: назад, номер страницы (без действия), вперёд (если есть следующая страница)

    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back")) # Добавление кнопки "Назад" для возврата
    return keyboard.as_markup() # Возврат готовой инлайн-клавиатуры

async def remind_tasks(tg_id, page=0):
    tasks = await get_tasks(tg_id) # Получение списка задач пользователя по его Telegram ID
    keyboard = InlineKeyboardBuilder() # Создание строителя инлайн-клавиатуры

    # Вычисление индексов для текущей страницы
    start_idx = page * TASKS_PER_PAGE # Вычисление начального индекса для текущей страницы
    end_idx = start_idx + TASKS_PER_PAGE # Вычисление конечного индекса для текущей страницы
    paginated_tasks = tasks[start_idx:end_idx] # Получение задач для текущей страницы

    # Добавление списка задач на свою отдельную строку
    for task in paginated_tasks: # Перебор задач на текущей странице
        keyboard.row(InlineKeyboardButton(
            text=f"⏰ {task.task}",
            callback_data=f'remind_{task.id}'
        )) # Добавление кнопки для установки напоминания для каждой задачи с её ID

    # Вычисление общего количества страниц
    total_pages = (len(tasks) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE # Вычисление количества страниц

    # Добавление кнопок навигации на последнюю строку
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
    ) # Добавление кнопок навигации: назад, номер страницы (без действия), вперёд (если есть следующая страница)
    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back")) # Добавление кнопки "Назад" для возврата
    return keyboard.as_markup() # Возврат готовой инлайн-клавиатуры

async def manage_reminders(tg_id, page=0):
    tasks = await get_tasks(tg_id) # Получение списка задач пользователя по его Telegram ID
    tasks_with_reminders = [task for task in tasks if task.reminders and any(r.is_active for r in task.reminders)] # Фильтрация задач с активными напоминаниями
    keyboard = InlineKeyboardBuilder() # Создание строителя инлайн-клавиатуры

    if not tasks_with_reminders: # Проверка наличия задач с активными напоминаниями
        keyboard.row(
            InlineKeyboardButton(text="Назад", callback_data="back"),
            InlineKeyboardButton(text="➕ Новое напоминание", callback_data="add_reminder")
        ) # Добавление кнопок "Назад" и "Новое напоминание", если напоминаний нет
        return keyboard.as_markup() # Возврат готовой инлайн-клавиатуры

    # Вычисление индексов для текущей страницы
    start_idx = page * TASKS_PER_PAGE # Вычисление начального индекса для текущей страницы
    end_idx = start_idx + TASKS_PER_PAGE # Вычисление конечного индекса для текущей страницы
    paginated_tasks = tasks_with_reminders[start_idx:end_idx] # Получение задач для текущей страницы

    for task in paginated_tasks: # Перебор задач на текущей странице
        for reminder in [r for r in task.reminders if r.is_active]: # Перебор активных напоминаний для каждой задачи
            reminder_time = reminder.remind_time.strftime("%d.%m.%Y %H:%M") # Форматирование времени напоминания
            keyboard.row(
                InlineKeyboardButton(
                    text=f"⏰ ({reminder_time}) {task.task}",
                    callback_data=f"select_reminder_{task.id}_{reminder.id}"
                )
            ) # Добавление кнопки для выбора напоминания с ID задачи и напоминания

    # Вычисление общего количества страниц
    total_pages = max(1, (len(tasks_with_reminders) + TASKS_PER_PAGE - 1) // TASKS_PER_PAGE) # Вычисление количества страниц

    # Добавление кнопок навигации
    nav_buttons = [] # Создание списка для навигационных кнопок
    if page > 0: # Проверка доступности предыдущей страницы
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"reminder_prev_{page}")) # Добавление кнопки "Назад"
    else:
        nav_buttons.append(InlineKeyboardButton(text="⬅️", callback_data="noop")) # Добавление неактивной кнопки "Назад"

    nav_buttons.append(InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data="noop"
    )) # Добавление кнопки с номером страницы (без действия)

    if end_idx < len(tasks_with_reminders): # Проверка доступности следующей страницы
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"reminder_next_{page}")) # Добавление кнопки "Вперёд"
    else:
        nav_buttons.append(InlineKeyboardButton(text="➡️", callback_data="noop")) # Добавление неактивной кнопки "Вперёд"

    keyboard.row(*nav_buttons) # Добавление строки с навигационными кнопками
    keyboard.row(InlineKeyboardButton(text="ㅤㅤ ㅤ               ➕ Новое напоминаниеㅤㅤ ㅤ               ", callback_data="add_reminder")) # Добавление кнопки для создания нового напоминания
    keyboard.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back")) # Добавление кнопки "Назад" для возврата

    return keyboard.as_markup() # Возврат готовой инлайн-клавиатуры