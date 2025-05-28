import asyncio
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.database.requests import del_task, set_task, set_user
from aiogram.enums import ChatAction
from app.states import TaskActions, Gen
from app.database.requests import update_task, get_task_by_id
import app.keyboards as kb
import app.database.requests as rq
from app.generate import ai_generate
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest
import logging

logging.basicConfig(level=logging.INFO) # Настройка базового уровня логирования на INFO
logger = logging.getLogger(__name__) # Создание логгера для записи событий текущего модуля

router = Router() # Создание роутера для обработки сообщений и callback-запросов


class Register(StatesGroup):
    name = State() # Состояние для ввода имени пользователя
    age = State() # Состояние для ввода возраста пользователя
    number = State() # Состояние для ввода номера телефона пользователя


@router.message(Command("start"))
async def start_cmd(message: Message):
    await set_user(message.from_user.id)  # Регистрация пользователя в базе данных по его Telegram ID
    await message.bot.send_chat_action(chat_id=message.from_user.id, action=ChatAction.TYPING) # Отображение анимации "печатает" в чате
    await asyncio.sleep(1) # Задержка в 1 секунду для имитации обработки
    welcome_text = (
        "👋 Добро пожаловать в ToDo Bot!\n\n"
        "Я помогу вам управлять задачами и напоминаниями. Вот что я умею:\n"
        "📋 Просматривать и добавлять задачи (/menu, /tasks)\n"
        "✏️ Изменять задачи\n"
        "❌ Удалять задачи\n"
        "⏰ Устанавливать напоминания\n"
        "🤖 Отвечать на запросы с помощью нейросети\n"
        "📢 Удалять все данные (/del)\n\n"
        "Нажмите 'Главное меню' или используйте /menu, чтобы начать!"
    ) # Текст приветственного сообщения с описанием возможностей бота
    await message.answer(welcome_text, reply_markup=kb.back_to_main) # Отправка приветственного сообщения с клавиатурой для возврата в меню


@router.message(Command("menu"))
async def menu_cmd(message: Message):
    await message.answer("Выберите пункт меню:", reply_markup=kb.inline_main) # Отправка сообщения с предложением выбрать пункт меню и инлайн-клавиатурой главного меню


@router.message(Command("tasks"))
async def tasks_cmd(message: Message):
    tasks = await rq.get_tasks(message.from_user.id) # Получение списка задач пользователя по его Telegram ID
    keyboard = await kb.my_task_kb(message.from_user.id) # Создание клавиатуры для управления задачами

    if not tasks: # Проверка, есть ли задачи у пользователя
        await message.answer(
            "📭 Список задач пуст",
            reply_markup=keyboard
        ) # Отправка сообщения о пустом списке задач с клавиатурой
        return # Завершение выполнения функции

    tasks_text = "📋 Ваши текущие задачи:\n\n" + "\n".join(f"▫️ {task.task}" for task in tasks) # Формирование текста со списком задач
    await message.answer(
        f"{tasks_text}\n\nВыберите действие:",
        reply_markup=keyboard
    ) # Отправка сообщения со списком задач и клавиатурой для выбора действия


@router.message(F.text == "Мои задачи")
async def show_tasks(message: Message):
    tasks = await rq.get_tasks(message.from_user.id) # Получение списка задач пользователя
    keyboard = await kb.my_task_kb(message.from_user.id) # Создание клавиатуры для управления задачами

    if not tasks: # Проверка, есть ли задачи у пользователя
        await message.answer(
            "📭 Список задач пуст",
            reply_markup=keyboard
        ) # Отправка сообщения о пустом списке задач с клавиатурой
        return # Завершение выполнения функции

    tasks_text = "📋 Ваши текущие задачи:\n\n" + "\n".join(f"▫️ {task.task}" for task in tasks) # Формирование текста со списком задач
    await message.answer(
        f"{tasks_text}\n\nВыберите действие:",
        reply_markup=keyboard
    ) # Отправка сообщения со списком задач и клавиатурой для выбора действия


@router.callback_query(F.data == 'my_task')
async def task(callback: CallbackQuery):
    tasks = await rq.get_tasks(callback.from_user.id) # Получение списка задач пользователя
    keyboard = await kb.my_task_kb(callback.from_user.id) # Создание клавиатуры для управления задачами

    if not tasks: # Проверка, есть ли задачи у пользователя
        await callback.message.edit_text(
            "📭 Список задач пуст",
            reply_markup=keyboard
        ) # Редактирование сообщения с информацией о пустом списке задач
        return await callback.answer() # Подтверждение обработки callback-запроса

    tasks_text = "📋 Ваши текущие задачи:\n\n" + "\n".join(f"▫️ {task.task}" for task in tasks) # Формирование текста со списком задач
    await callback.message.edit_text(
        f"{tasks_text}\n\nВыберите действие:",
        reply_markup=keyboard
    ) # Редактирование сообщения со списком задач и клавиатурой
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data == 'back')
async def return_back(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state() # Получение текущего состояния FSM

    try: # Начало блока обработки ошибок
        if current_state == Gen.wait: # Проверка, находится ли бот в состоянии ожидания запроса к ИИ
            await state.clear() # Очистка текущего состояния
            # Проверка, нужно ли обновлять содержимое сообщения
            if callback.message.text != 'Выберите пункт меню' or callback.message.reply_markup != kb.inline_main:
                await callback.message.edit_text('Выберите пункт меню', reply_markup=kb.inline_main) # Редактирование сообщения с главным меню
        elif current_state in [TaskActions.adding, TaskActions.reminder_time, TaskActions.edit_reminder,
                               Gen.conversation]: # Проверка, находится ли бот в состояниях добавления задачи, установки времени или разговора с ИИ
            await state.clear() # Очистка текущего состояния
            tasks = await rq.get_tasks(callback.from_user.id) # Получение списка задач пользователя
            keyboard = await kb.my_task_kb(callback.from_user.id) # Создание клавиатуры для управления задачами
            text = "📭 Список задач пуст" if not tasks else "📋 Ваши текущие задачи:\n\n" + "\n".join(
                f"▫️ {task.task}" for task in tasks) + "\n\nВыберите действие:" # Формирование текста в зависимости от наличия задач

            # Проверка, нужно ли обновлять содержимое сообщения
            if callback.message.text != text or callback.message.reply_markup != keyboard:
                await callback.message.edit_text(text, reply_markup=keyboard) # Редактирование сообщения со списком задач
        else: # Обработка остальных случаев
            # Проверка, нужно ли обновлять содержимое сообщения
            if callback.message.text != 'Выберите пункт меню' or callback.message.reply_markup != kb.inline_main:
                await callback.message.edit_text('Выберите пункт меню', reply_markup=kb.inline_main) # Редактирование сообщения с главным меню

        try: # Проверка возможности подтверждения callback-запроса
            await callback.answer()  # Подтверждение обработки callback-запроса (убирает анимацию загрузки)
        except TelegramBadRequest as e: # Перехват ошибки при подтверждении callback
            logger.warning(f"Failed to answer callback query: {e}") # Запись предупреждения в лог

    except TelegramBadRequest as e: # Перехват ошибки при редактировании сообщения
        logger.error(f"Failed to edit message in return_back: {e}") # Запись ошибки в лог
        # Резервный вариант: отправка нового сообщения
        await callback.message.answer(
            "⚠️ Не удалось обновить сообщение. Выберите пункт меню:",
            reply_markup=kb.inline_main
        ) # Отправка нового сообщения с главным меню
        await state.clear() # Очистка текущего состояния


@router.message(F.text == "Главное меню")
async def main_menu(message: Message):
    await message.answer("Выберите пункт меню:", reply_markup=kb.inline_main) # Отправка сообщения с главным меню и инлайн-клавиатурой


@router.callback_query(F.data == 'ai_req')
async def ai_generating(callback: CallbackQuery, state: FSMContext):
    welcome_message = (
        "👋 Привет! Я 'Ассистент Тудушка', ваш ИИ-помощник по планированию времени и управлению задачами. Я могу помочь вам с: \n"
        "- Советы по тайм-менеджменту и продуктивности. \n"
        "- Разбиение больших задач на более мелкие шаги. \n"
        "- Планирование вашего дня, недели или месяца. \n"
        "- Использование функций бота для управления вашими задачами и напоминаниями. \n"
        "Просто напишите свой вопрос или запрос, и я сделаю все возможное, чтобы помочь вам! Если вы хотите начать новый разговор, нажмите 'Новый чат'."
    ) # Текст приветственного сообщения для ИИ-ассистента
    try: # Начало блока обработки ошибок
        await callback.message.edit_text(
            welcome_message,
            reply_markup=kb.ai_cancel
        ) # Редактирование сообщения с приветствием ИИ-ассистента и клавиатурой отмены
        await state.set_state(Gen.wait) # Установка состояния ожидания запроса к ИИ
        await state.update_data(conversation_history=[]) # Инициализация пустой истории разговора
        try: # Проверка возможности подтверждения callback
            await callback.answer()  # Подтверждение обработки callback-запроса
        except TelegramBadRequest as e: # Перехват ошибки при подтверждении callback
            logger.warning(f"Failed to answer callback query: {e}") # Запись предупреждения в лог
    except TelegramBadRequest as e: # Перехват ошибки при редактировании сообщения
        logger.error(f"Failed to edit message in ai_generating: {e}") # Запись ошибки в лог
        await callback.message.answer(
            "⚠️ Произошла ошибка при открытии ИИ-ассистента. Попробуйте снова.",
            reply_markup=kb.inline_main
        ) # Отправка сообщения об ошибке с главным меню
        await state.clear() # Очистка текущего состояния


@router.message(Gen.wait)
async def process_ai_request(message: Message, state: FSMContext):
    msg = await message.answer("⏳ Ваш запрос обрабатывается...", reply_markup=kb.ai_conversation) # Отправка временного сообщения с индикацией обработки

    try: # Начало блока обработки ошибок
        data = await state.get_data() # Получение данных состояния
        conversation_history = data.get('conversation_history', []) # Получение истории разговора или пустого списка
        conversation_history.append({"role": "user", "content": message.text}) # Добавление пользовательского сообщения в историю

        response = await ai_generate(conversation_history) # Вызов функции генерации ответа от ИИ
        if not response or response.strip() == "": # Проверка, получен ли пустой ответ
            logger.error("Empty response from ai_generate") # Запись ошибки в лог
            await msg.delete() # Удаление временного сообщения
            await message.answer(
                "⚠️ Не удалось получить ответ от ИИ. Пожалуйста, попробуйте снова.",
                reply_markup=kb.ai_conversation
            ) # Отправка сообщения об ошибке
            return # Завершение выполнения функции

        conversation_history.append({"role": "assistant", "content": response}) # Добавление ответа ИИ в историю
        await state.update_data(conversation_history=conversation_history) # Обновление истории разговора в состоянии

        await msg.delete() # Удаление временного сообщения
        await message.answer(
            text=response,
            reply_markup=kb.ai_conversation,
            parse_mode='Markdown'
        ) # Отправка ответа ИИ с клавиатурой для продолжения разговора
        await state.set_state(Gen.conversation) # Переход в состояние активного разговора с ИИ
    except Exception as e: # Перехват любых других ошибок
        logger.error(f"Error in process_ai_request: {e}") # Запись ошибки в лог
        await msg.delete() # Удаление временного сообщения
        await message.answer(
            f"⚠️ Произошла ошибка: {str(e)}",
            reply_markup=kb.back_to_main
        ) # Отправка сообщения об ошибке с клавиатурой возврата
        await state.clear() # Очистка текущего состояния


@router.message(Gen.conversation)
async def continue_ai_conversation(message: Message, state: FSMContext):
    if message.text == "Новый чат": # Проверка, хочет ли пользователь начать новый чат
        await state.update_data(conversation_history=[]) # Сброс истории разговора
        await message.answer(
            "✅ Новый чат начат. Напишите ваш запрос:",
            reply_markup=kb.ai_conversation
        ) # Отправка сообщения о начале нового чата
        await state.set_state(Gen.wait) # Переход в состояние ожидания запроса
        return # Завершение выполнения функции

    if message.text in ["Главное меню", "Мои задачи"]: # Проверка, хочет ли пользователь выйти в меню или задачи
        await state.clear() # Очистка текущего состояния
        temp_msg = await message.answer("Переход...", reply_markup=ReplyKeyboardRemove()) # Отправка временного сообщения с удалением клавиатуры
        await temp_msg.delete() # Удаление временного сообщения
        if message.text == "Главное меню": # Проверка перехода в главное меню
            await message.answer("Выберите пункт меню:", reply_markup=kb.inline_main) # Отправка сообщения с главным меню
        else: # Обработка перехода к задачам
            tasks = await rq.get_tasks(message.from_user.id) # Получение списка задач
            keyboard = await kb.my_task_kb(message.from_user.id) # Создание клавиатуры для задач
            text = "📭 Список задач пуст" if not tasks else "📋 Ваши текущие задачи:\n\n" + "\n".join(
                f"▫️ {task.task}" for task in tasks) # Формирование текста в зависимости от наличия задач
            await message.answer(
                f"{text}\n\nВыберите действие:",
                reply_markup=keyboard
            ) # Отправка сообщения со списком задач
        return # Завершение выполнения функции

    msg = await message.answer("⏳ Ваш запрос обрабатывается...", reply_markup=kb.ai_conversation) # Отправка временного сообщения с индикацией обработки

    try: # Начало блока обработки ошибок
        data = await state.get_data() # Получение данных состояния
        conversation_history = data.get('conversation_history', []) # Получение истории разговора
        conversation_history.append({"role": "user", "content": message.text}) # Добавление пользовательского сообщения

        response = await ai_generate(conversation_history) # Вызов функции генерации ответа от ИИ
        if not response or response.strip() == "": # Проверка, получен ли пустой ответ
            logger.error("Empty response from ai_generate") # Запись ошибки в лог
            await msg.delete() # Удаление временного сообщения
            await message.answer(
                "⚠️ Не удалось получить ответ от ИИ. Пожалуйста, попробуйте снова.",
                reply_markup=kb.ai_conversation
            ) # Отправка сообщения об ошибке
            return # Завершение выполнения функции

        conversation_history.append({"role": "assistant", "content": response}) # Добавление ответа ИИ в историю
        await state.update_data(conversation_history=conversation_history) # Обновление истории разговора

        await msg.delete() # Удаление временного сообщения
        await message.answer(
            text=response,
            reply_markup=kb.ai_conversation,
            parse_mode='Markdown'
        ) # Отправка ответа ИИ с клавиатурой для продолжения разговора
    except Exception as e: # Перехват любых ошибок
        logger.error(f"Error in continue_ai_conversation: {e}") # Запись ошибки в лог
        await msg.delete() # Удаление временного сообщения
        await message.answer(
            f"⚠️ Произошла ошибка: {str(e)}",
            reply_markup=kb.ai_conversation
        ) # Отправка сообщения об ошибке


@router.message(Command("del"))
async def clear_data(message: Message, state: FSMContext):
    tasks = await rq.get_tasks(message.from_user.id) # Получение списка задач пользователя
    if not tasks: # Проверка, есть ли задачи для удаления
        await message.answer("❌ У вас нет задач для удаления", reply_markup=kb.back_to_main) # Отправка сообщения об отсутствии задач
        return # Завершение выполнения функции

    await state.set_state(TaskActions.deleting) # Установка состояния удаления задач
    await message.answer(
        "⚠️ Вы уверены, что хотите удалить все свои задачи? Это действие нельзя отменить.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="Да, удалить", callback_data="confirm_delete"),
                    InlineKeyboardButton(text="Нет, отменить", callback_data="cancel_delete")
                ]
            ]
        )
    ) # Отправка запроса на подтверждение удаления с инлайн-клавиатурой


@router.callback_query(F.data == "confirm_delete")
async def confirm_delete_tasks(callback: CallbackQuery, state: FSMContext):
    success = await rq.delete_user_data(callback.from_user.id) # Удаление всех данных пользователя
    await state.clear() # Очистка текущего состояния
    if success: # Проверка успешности удаления
        await callback.message.edit_text(
            "✅ Все ваши задачи удалены!",
            reply_markup=kb.inline_main
        ) # Редактирование сообщения с подтверждением удаления
    else: # Обработка случая, если данные не были удалены
        await callback.message.edit_text(
            "❌ У вас нет задач для удаления",
            reply_markup=kb.inline_main
        ) # Редактирование сообщения об отсутствии задач
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete_tasks(callback: CallbackQuery, state: FSMContext):
    await state.clear() # Очистка текущего состояния
    await callback.message.edit_text(
        "✅ Удаление отменено",
        reply_markup=kb.inline_main
    ) # Редактирование сообщения с подтверждением отмены
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data == 'add')
async def add_task(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskActions.adding) # Установка состояния добавления задачи
    await callback.message.edit_text(
        "Введите текст новой задачи:",
        reply_markup=kb.back_button
    ) # Редактирование сообщения с запросом текста задачи
    await callback.answer() # Подтверждение обработки callback-запроса


@router.message(TaskActions.adding)
async def task_added(message: Message, state: FSMContext):
    if message.text == "Назад": # Проверка, хочет ли пользователь отменить добавление
        await state.clear() # Очистка текущего состояния
        tasks = await rq.get_tasks(message.from_user.id) # Получение списка задач
        keyboard = await kb.my_task_kb(message.from_user.id) # Создание клавиатуры для задач
        text = "📭 Список задач пуст" if not tasks else "📋 Ваши текущие задачи:\n\n" + "\n".join(
            f"▫️ {task.task}" for task in tasks) # Формирование текста в зависимости от наличия задач
        await message.answer(
            f"{text}\n\nВыберите действие:",
            reply_markup=keyboard
        ) # Отправка сообщения со списком задач
        return # Завершение выполнения функции

    try: # Начало блока обработки ошибок
        task_id = await set_task(message.from_user.id, message.text) # Добавление новой задачи в базу данных
        await state.update_data(new_task_id=task_id) # Сохранение ID новой задачи в состоянии
        await message.answer(
            "✅ Задача добавлена! Хотите установить напоминание?",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="Да", callback_data="remind_yes"),
                        InlineKeyboardButton(text="Нет", callback_data="remind_no")
                    ]
                ]
            )
        ) # Отправка сообщения с запросом на установку напоминания
        await state.set_state(TaskActions.ask_reminder) # Переход в состояние запроса напоминания
    except Exception as e: # Перехват любых ошибок
        await message.answer(
            f"❌ Не удалось добавить задачу: {str(e)}",
            reply_markup=kb.back_to_main
        ) # Отправка сообщения об ошибке
        await state.clear() # Очистка текущего состояния


@router.callback_query(F.data == "remind_yes", TaskActions.ask_reminder)
async def confirm_reminder(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data() # Получение данных состояния
    task_id = data.get('new_task_id') # Извлечение ID новой задачи

    await state.update_data(task_id=task_id) # Обновление данных состояния с ID задачи
    await state.set_state(TaskActions.reminder_time) # Переход в состояние установки времени напоминания

    await callback.message.edit_text(
        "Выберите время напоминания или введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 28.05.2025 15:30):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="через 1 час", callback_data="remind_in_1h"),
                    InlineKeyboardButton(text="через 3 часа", callback_data="remind_in_3h")
                ],
                [
                    InlineKeyboardButton(text="через 12 часов", callback_data="remind_in_12h"),
                    InlineKeyboardButton(text="через 24 часа", callback_data="remind_in_24h")
                ],
                [
                    InlineKeyboardButton(text="через неделю (7 дней)", callback_data="remind_in_7d"),
                    InlineKeyboardButton(text="через месяц (30 дней)", callback_data="remind_in_30d")
                ],
                [InlineKeyboardButton(text="Назад", callback_data="back")]
            ]
        )
    ) # Редактирование сообщения с выбором времени напоминания
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data == "remind_no", TaskActions.ask_reminder)
async def cancel_reminder(callback: CallbackQuery, state: FSMContext):
    await state.clear() # Очистка текущего состояния
    await callback.message.edit_text(
        "✅ Задача сохранена без напоминания!",
        reply_markup=kb.inline_main
    ) # Редактирование сообщения с подтверждением сохранения без напоминания
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data.regexp(r'^delete_(0|prev_\d+|next_\d+)$'))
async def delete_task_menu(callback: CallbackQuery):
    if callback.data == 'delete_0': # Проверка, запрошена ли первая страница
        page = 0 # Установка номера страницы на 0
    elif callback.data.startswith('delete_prev_') or callback.data.startswith('delete_next_'): # Проверка навигации по страницам
        page = int(callback.data.split('_')[2]) # Извлечение номера текущей страницы
        if callback.data.startswith('delete_prev_') and page == 0: # Проверка попытки перехода назад с первой страницы
            await callback.answer("Это первая страница!", show_alert=False) # Отправка уведомления
            return # Завершение выполнения функции
        page = max(0, page - 1) if callback.data.startswith('delete_prev_') else page + 1 # Уменьшение или увеличение номера страницы
    else: # Обработка других случаев
        page = int(callback.data.split('_')[1]) # Извлечение номера страницы
    tasks_markup = await kb.delete_tasks(callback.from_user.id, page) # Создание клавиатуры для удаления задач
    await callback.message.edit_text("Выберите задачу для удаления:", reply_markup=tasks_markup) # Редактирование сообщения с выбором задачи
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data.regexp(r'^delete_\d+$'))
async def delete_selected_task(callback: CallbackQuery):
    task_id = int(callback.data.split('_')[1]) # Извлечение ID задачи из callback-данных
    success = await del_task(task_id) # Удаление задачи из базы данных
    if success: # Проверка успешности удаления
        new_kb = await kb.my_task_kb(callback.from_user.id) # Создание обновлённой клавиатуры для задач
        await callback.message.edit_text("✅ Задача удалена!", reply_markup=new_kb) # Редактирование сообщения с подтверждением
    else: # Обработка случая, если задача не найдена
        await callback.message.edit_text("❌ Задача не найдена", reply_markup=kb.back_button) # Редактирование сообщения об ошибке
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data.regexp(r'^change_(0|prev_\d+|next_\d+)$'))
async def change_task_menu(callback: CallbackQuery):
    if callback.data == 'change_0': # Проверка, запрошена ли первая страница
        page = 0 # Установка номера страницы на 0
    elif callback.data.startswith('change_prev_') or callback.data.startswith('change_next_'): # Проверка навигации по страницам
        page = int(callback.data.split('_')[2]) # Извлечение номера текущей страницы
        if callback.data.startswith('change_prev_') and page == 0: # Проверка попытки перехода назад с первой страницы
            await callback.answer("Это первая страница!", show_alert=False) # Отправка уведомления
            return # Завершение выполнения функции
        page = max(0, page - 1) if callback.data.startswith('change_prev_') else page + 1 # Уменьшение или увеличение номера страницы
    else: # Обработка других случаев
        page = int(callback.data.split('_')[1]) # Извлечение номера страницы
    tasks_markup = await kb.edit_tasks(callback.from_user.id, page) # Создание клавиатуры для редактирования задач
    await callback.message.edit_text("Выберите задачу для изменения:", reply_markup=tasks_markup) # Редактирование сообщения с выбором задачи
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data.startswith('change_'))
async def select_task_to_edit(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split('_')[1]) # Извлечение ID задачи
    await state.update_data(task_id=task_id) # Сохранение ID задачи в состоянии
    await state.set_state(TaskActions.new_text) # Переход в состояние ввода нового текста задачи
    await callback.message.edit_text("Введите новый текст задачи:", reply_markup=kb.back_button) # Редактирование сообщения с запросом нового текста
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data == 'contact')
async def contact(callback: CallbackQuery):
    await callback.message.edit_text('По всем вопросам обращайтесь к создателям бота: '
                                     '\n <a href="https://t.me/sadmenus">Роман</a>'
                                     '\n <a href="https://t.me/michaelj_ordan">Микаэль</a>'
                                     '\n <a href="https://t.me/sziixubs">Дмитрий</a>'
                                     '\n <a href="https://t.me/just_m1chael">Михаил</a>'
                                     '\n Канал главного дизайнера: '
                                     '\n @me_ananasik'
                                     '\n Подпишитесь 😊',
                                     reply_markup=kb.back_button,
                                     parse_mode='HTML') # Редактирование сообщения с контактами разработчиков


@router.callback_query(F.data == 'feedback')
async def feedback(callback: CallbackQuery):
    await callback.message.edit_text('📋Пройдите опрос, связанный с нашим ботом'
                                     '\nНам важно ваше мнение🙏'
                                     '\n https://forms.gle/gf5xcFqHR8kGkh9H7', reply_markup=kb.back_button) # Редактирование сообщения с ссылкой на форму обратной связи


@router.message(TaskActions.new_text)
async def save_updated_task(message: Message, state: FSMContext):
    data = await state.get_data() # Получение данных состояния
    task_id = data.get('task_id') # Извлечение ID задачи
    new_text = message.text # Получение нового текста задачи
    if not task_id: # Проверка наличия ID задачи
        await message.answer("❌ Ошибка: задача не найдена", reply_markup=kb.back_to_main) # Отправка сообщения об ошибке
        await state.clear() # Очистка текущего состояния
        return # Завершение выполнения функции

    success = await update_task(task_id, new_text) # Обновление текста задачи в базе данных
    if success: # Проверка успешности обновления
        new_kb = await kb.my_task_kb(message.from_user.id) # Создание обновлённой клавиатуры для задач
        await message.answer("✅ Задача изменена!", reply_markup=new_kb) # Отправка сообщения с подтверждением
    else: # Обработка случая, если задача не найдена
        await message.answer("❌ Ошибка: задача не найдена", reply_markup=kb.back_to_main) # Отправка сообщения об ошибке
    await state.clear() # Очистка текущего состояния


@router.callback_query(F.data.regexp(r'^remind_(0|prev_\d+|next_\d+)$'))
async def remind_task_menu(callback: CallbackQuery):
    if callback.data == 'remind_0': # Проверка, запрошена ли первая страница
        page = 0 # Установка номера страницы на 0
    elif callback.data.startswith('remind_prev_') or callback.data.startswith('remind_next_'): # Проверка навигации по страницам
        page = int(callback.data.split('_')[2]) # Извлечение номера текущей страницы
        if callback.data.startswith('remind_prev_') and page == 0: # Проверка попытки перехода назад с первой страницы
            await callback.answer("Это первая страница!", show_alert=False) # Отправка уведомления
            return # Завершение выполнения функции
        page = max(0, page - 1) if callback.data.startswith('remind_prev_') else page + 1 # Уменьшение или увеличение номера страницы
    else: # Обработка других случаев
        page = int(callback.data.split('_')[1]) # Извлечение номера страницы
    tasks_markup = await kb.remind_tasks(callback.from_user.id, page) # Создание клавиатуры для установки напоминаний
    await callback.message.edit_text("Выберите задачу для напоминания:", reply_markup=tasks_markup) # Редактирование сообщения с выбором задачи
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data.regexp(r'^remind_\d+$'))
async def select_task_to_remind(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split('_')[1]) # Извлечение ID задачи
    await state.update_data(task_id=task_id) # Сохранение ID задачи в состоянии
    await state.set_state(TaskActions.reminder_time) # Переход в состояние установки времени напоминания
    await callback.message.edit_text(
        "Выберите время напоминания или введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 28.05.2025 15:30):",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="через 1 час", callback_data="remind_in_1h"),
                    InlineKeyboardButton(text="через 3 часа", callback_data="remind_in_3h")
                ],
                [
                    InlineKeyboardButton(text="через 12 часов", callback_data="remind_in_12h"),
                    InlineKeyboardButton(text="через 24 часа", callback_data="remind_in_24h")
                ],
                [
                    InlineKeyboardButton(text="через неделю (7 дней)", callback_data="remind_in_7d"),
                    InlineKeyboardButton(text="через месяц (30 дней)", callback_data="remind_in_30d")
                ],
                [InlineKeyboardButton(text="Назад", callback_data="back")]
            ]
        )
    ) # Редактирование сообщения с выбором времени напоминания
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data.startswith('remind_in_'))
async def quick_set_reminder(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data() # Получение данных состояния
    task_id = data.get('task_id') # Извлечение ID задачи
    if not task_id: # Проверка наличия ID задачи
        await callback.message.edit_text("❌ Ошибка: задача не найдена", reply_markup=kb.back_button) # Редактирование сообщения об ошибке
        await state.clear() # Очистка текущего состояния
        await callback.answer() # Подтверждение обработки callback-запроса
        return # Завершение выполнения функции

    interval = callback.data.split('_')[-1] # Извлечение интервала времени из callback-данных
    current_time = datetime.now() # Получение текущего времени
    if interval == "1h": # Проверка интервала в 1 час
        remind_time = current_time + timedelta(hours=1) # Установка времени напоминания через 1 час
    elif interval == "3h": # Проверка интервала в 3 часа
        remind_time = current_time + timedelta(hours=3) # Установка времени напоминания через 3 часа
    elif interval == "12h": # Проверка интервала в 12 часов
        remind_time = current_time + timedelta(hours=12) # Установка времени напоминания через 12 часов
    elif interval == "24h": # Проверка интервала в 24 часа
        remind_time = current_time + timedelta(hours=24) # Установка времени напоминания через 24 часа
    elif interval == "7d": # Проверка интервала в 7 дней
        remind_time = current_time + timedelta(days=7) # Установка времени напоминания через 7 дней
    elif interval == "30d": # Проверка интервала в 30 дней
        remind_time = current_time + timedelta(days=30) # Установка времени напоминания через 30 дней
    else: # Обработка неверного интервала
        await callback.message.edit_text("❌ Неверный интервал", reply_markup=kb.back_button) # Редактирование сообщения об ошибке
        await state.clear() # Очистка текущего состояния
        await callback.answer() # Подтверждение обработки callback-запроса
        return # Завершение выполнения функции

    await rq.set_reminder(task_id, remind_time) # Установка напоминания в базе данных
    await callback.message.edit_text(
        f"⏰ Напоминание установлено на {remind_time.strftime('%d.%m.%Y %H:%M')}!",
        reply_markup=kb.inline_main
    ) # Редактирование сообщения с подтверждением времени напоминания
    await state.clear() # Очистка текущего состояния
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data.startswith('delete_after_reminder_') | F.data.startswith('keep_after_reminder_'))
async def handle_reminder_action(callback: CallbackQuery):
    action, task_id = callback.data.split('_')[0], int(callback.data.split('_')[3]) # Извлечение действия и ID задачи

    if action == 'delete': # Проверка, выбрано ли удаление задачи
        success = await del_task(task_id) # Удаление задачи из базы данных
        if success: # Проверка успешности удаления
            await callback.message.edit_text("✅ Задача удалена!", reply_markup=kb.back_button) # Редактирование сообщения с подтверждением
            await callback.message.answer("Выберите действие:", reply_markup=kb.back_to_main) # Отправка сообщения с клавиатурой возврата
        else: # Обработка случая, если задача не найдена
            await callback.message.edit_text("❌ Задача не найдена", reply_markup=kb.back_button) # Редактирование сообщения об ошибке
            await callback.message.answer("Выберите действие:", reply_markup=kb.back_to_main) # Отправка сообщения с клавиатурой возврата
    else:  # Обработка действия "оставить задачу"
        await callback.message.edit_text("✅ Задача оставлена в списке.", reply_markup=kb.back_button) # Редактирование сообщения с подтверждением
        await callback.message.answer("Выберите действие:", reply_markup=kb.back_to_main) # Отправка сообщения с клавиатурой возврата

    await callback.answer() # Подтверждение обработки callback-запроса


@router.message(TaskActions.reminder_time)
async def save_reminder(message: Message, state: FSMContext):
    if message.text == "Назад": # Проверка, хочет ли пользователь отменить установку напоминания
        await state.clear() # Очистка текущего состояния
        tasks = await rq.get_tasks(message.from_user.id) # Получение списка задач
        keyboard = await kb.my_task_kb(message.from_user.id) # Создание клавиатуры для задач
        text = "📭 Список задач пуст" if not tasks else "📋 Ваши текущие задачи:\n\n" + "\n".join(
            f"▫️ {task.task}" for task in tasks) # Формирование текста в зависимости от наличия задач
        await message.answer(
            f"{text}\n\nВыберите действие:",
            reply_markup=keyboard
        ) # Отправка сообщения со списком задач
        return # Завершение выполнения функции

    if validate_date_time(message.text): # Проверка корректности введённого времени
        try: # Начало блока обработки ошибок
            remind_time = datetime.strptime(message.text, "%d.%m.%Y %H:%M") # Парсинг введённой даты и времени
        except ValueError: # Перехват ошибки парсинга
            await message.answer("❌ Неверный формат! Используйте ДД.ММ.ГГГГ ЧЧ:ММ, например, 28.05.2025 15:30",
                                 reply_markup=kb.back_button) # Отправка сообщения об ошибке
            return # Завершение выполнения функции

        data = await state.get_data() # Получение данных состояния
        task_id = data.get('task_id') # Извлечение ID задачи

        await rq.set_reminder(task_id, remind_time) # Установка напоминания в базе данных
        await message.answer(
            f"⏰ Напоминание установлено на {remind_time.strftime('%d.%m.%Y %H:%M')}!",
            reply_markup=kb.inline_main
        ) # Отправка сообщения с подтверждением
        await state.clear() # Очистка текущего состояния
    else: # Обработка некорректного формата или времени в прошлом
        await message.answer("❌ Неверный формат или время в прошлом! Используйте ДД.ММ.ГГГГ ЧЧ:ММ, например,"
                             "28.05.2025 15:30", reply_markup=kb.back_button) # Отправка сообщения об ошибке


def validate_date_time(input_str):
    try: # Начало блока обработки ошибок
        input_str = input_str.strip() # Удаление пробелов в начале и конце строки
        date_str, time_str = input_str.split() # Разделение строки на дату и время
        input_datetime = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M") # Парсинг даты и времени
        current_datetime = datetime.now() # Получение текущего времени
        if input_datetime <= current_datetime: # Проверка, не находится ли время в прошлом
            return False # Возврат False, если время в прошлом
        return True # Возврат True, если формат корректен и время в будущем
    except ValueError: # Перехват ошибки парсинга
        return False # Возврат False при неверном формате


@router.callback_query(F.data == 'view_reminders')
async def view_reminders(callback: CallbackQuery):
    keyboard = await kb.manage_reminders(callback.from_user.id) # Создание клавиатуры для управления напоминаниями
    await callback.message.edit_text("📅 Активные напоминания:", reply_markup=keyboard) # Редактирование сообщения с активными напоминаниями
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data.regexp(r'^reminder_(prev|next)_(\d+)$'))
async def paginate_reminders(callback: CallbackQuery):
    try: # Начало блока обработки ошибок
        action, current_page = callback.data.split('_')[1], int(callback.data.split('_')[2]) # Извлечение действия и номера страницы
        tasks = await rq.get_tasks(callback.from_user.id) # Получение списка задач
        tasks_with_reminders = [task for task in tasks if task.reminders and any(r.is_active for r in task.reminders)] # Фильтрация задач с активными напоминаниями
        total_pages = max(1, (len(tasks_with_reminders) + kb.TASKS_PER_PAGE - 1) // kb.TASKS_PER_PAGE) # Вычисление общего количества страниц

        new_page = current_page - 1 if action == "prev" else current_page + 1 # Определение новой страницы

        if action == "prev" and current_page == 0: # Проверка попытки перехода назад с первой страницы
            await callback.answer("Это первая страница!", show_alert=True) # Отправка уведомления
            return # Завершение выполнения функции

        if action == "next" and current_page >= total_pages - 1: # Проверка попытки перехода вперёд с последней страницы
            await callback.answer(
                "У вас пока нет нужного количества задач для перехода на следующую страницу",
                show_alert=True
            ) # Отправка уведомления
            return # Завершение выполнения функции

        new_page = max(0, new_page) # Убедиться, что номер страницы не отрицательный
        keyboard = await kb.manage_reminders(callback.from_user.id, new_page) # Создание клавиатуры для новой страницы
        if keyboard != callback.message.reply_markup: # Проверка, отличается ли новая клавиатура
            await callback.message.edit_reply_markup(reply_markup=keyboard) # Обновление клавиатуры сообщения
        await callback.answer() # Подтверждение обработки callback-запроса

    except ValueError as e: # Перехват ошибки обработки страницы
        await callback.answer(f"Ошибка обработки страницы: {str(e)}", show_alert=True) # Отправка уведомления об ошибке
    except Exception as e: # Перехват любых других ошибок
        await callback.answer(f"Произошла ошибка: {str(e)}", show_alert=True) # Отправка уведомления об ошибке


@router.callback_query(F.data.startswith('remove_reminder_'))
async def remove_reminder(callback: CallbackQuery):
    reminder_id = int(callback.data.split('_')[2]) # Извлечение ID напоминания
    success = await rq.deactivate_reminder(reminder_id) # Деактивация напоминания в базе данных

    if success: # Проверка успешности деактивации
        keyboard = await kb.manage_reminders(callback.from_user.id) # Создание обновлённой клавиатуры для напоминаний
        await callback.message.edit_text("📅 Активные напоминания:", reply_markup=keyboard) # Редактирование сообщения с активными напоминаниями
        await callback.answer("✅ Напоминание удалено!") # Подтверждение удаления
    else: # Обработка случая, если напоминание не найдено
        await callback.answer("❌ Напоминание не найдено", show_alert=True) # Отправка уведомления об ошибке


@router.callback_query(F.data.startswith('edit_reminder_'))
async def edit_reminder(callback: CallbackQuery, state: FSMContext):
    try: # Начало блока обработки ошибок
        reminder_id = int(callback.data.split('_')[-1]) # Извлечение ID напоминания
        task_id = int(callback.data.split('_')[-2]) # Извлечение ID задачи
        task = await get_task_by_id(task_id) # Получение задачи по ID
        if not task: # Проверка существования задачи
            await callback.message.edit_text("❌ Задача не найдена", reply_markup=kb.back_button) # Редактирование сообщения об ошибке
            await callback.answer("Задача не найдена", show_alert=True) # Отправка уведомления
            return # Завершение выполнения функции

        reminder = next((r for r in task.reminders if r.id == reminder_id and r.is_active), None) # Поиск активного напоминания
        if not reminder: # Проверка существования напоминания
            await callback.message.edit_text(
                "❌ Напоминание не найдено. Хотите создать новое?",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Создать напоминание", callback_data=f"remind_{task_id}")],
                        [InlineKeyboardButton(text="Назад", callback_data="view_reminders")]
                    ]
                )
            ) # Редактирование сообщения с предложением создать новое напоминание
            await callback.answer("Напоминание не найдено", show_alert=True) # Отправка уведомления
            return # Завершение выполнения функции

        await state.update_data(task_id=task_id, reminder_id=reminder_id) # Сохранение ID задачи и напоминания в состоянии
        await state.set_state(TaskActions.edit_reminder) # Переход в состояние редактирования напоминания

        current_time = reminder.remind_time.strftime("%d.%m.%Y %H:%M") # Форматирование текущего времени напоминания
        await callback.message.edit_text(
            f"✏️ Текущее время напоминания: {current_time}\n"
            "Введите новое время в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.12.2023 15:30):",
            reply_markup=kb.back_button
        ) # Редактирование сообщения с запросом нового времени
        await callback.answer() # Подтверждение обработки callback-запроса

    except ValueError: # Перехват ошибки неверного формата ID
        await callback.message.edit_text("❌ Ошибка: Неверный формат идентификатора", reply_markup=kb.back_button) # Редактирование сообщения об ошибке
        await callback.answer("Ошибка обработки запроса", show_alert=True) # Отправка уведомления
    except Exception as e: # Перехват других ошибок
        await callback.message.edit_text("❌ Произошла ошибка при попытке редактирования", reply_markup=kb.back_button) # Редактирование сообщения об ошибке
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True) # Отправка уведомления


@router.message(TaskActions.edit_reminder)
async def save_updated_reminder(message: Message, state: FSMContext):
    data = await state.get_data() # Получение данных состояния
    task_id = data.get('task_id') # Извлечение ID задачи
    reminder_id = data.get('reminder_id') # Извлечение ID напоминания

    if not task_id or not reminder_id: # Проверка наличия ID задачи и напоминания
        await message.answer("⚠️ Ошибка: задача или напоминание не найдены", reply_markup=kb.back_to_main) # Отправка сообщения об ошибке
        await state.clear() # Очистка текущего состояния
        return # Завершение выполнения функции

    if message.text == "Назад": # Проверка, хочет ли пользователь отменить редактирование
        await state.clear() # Очистка текущего состояния
        tasks = await rq.get_tasks(message.from_user.id) # Получение списка задач
        keyboard = await kb.my_task_kb(message.from_user.id) # Создание клавиатуры для задач
        text = "📭 Список задач пуст" if not tasks else "📋 Ваши текущие задачи:\n\n" + "\n".join(
            f"▫️ {task.task}" for task in tasks) # Формирование текста сообщения
        await message.answer(
            f"{text}\n\nВыберите действие:",
            reply_markup=keyboard
        ) # Отправка сообщения со списком задач
        return # Завершение выполнения функции

    try: # Начало блока обработки ошибок
        if not validate_date_time(message.text): # Проверка корректности введённого времени
            await message.answer(
                "❌ Неверный формат или время в прошлом! Используйте ДД.ММ.ГГГГ ЧЧ:ММ, например, 25.12.2023 15:30",
                reply_markup=kb.back_button
            ) # Отправка сообщения об ошибке
            return # Завершение выполнения функции

        new_time = datetime.strptime(message.text, "%d.%m.%Y %H:%M") # Парсинг нового времени
        success = await rq.update_reminder_time(reminder_id, new_time) # Обновление времени напоминания в базе данных

        if success: # Проверка успешности обновления
            await message.answer(
                f"✅ Напоминание обновлено на {new_time.strftime('%d.%m.%Y %H:%M')}!",
                reply_markup=kb.inline_main
            ) # Отправка сообщения с подтверждением
        else: # Обработка случая, если напоминание не найдено
            await message.answer(
                f"❌ Ошибка: напоминание не найдено",
                reply_markup=kb.inline_main
            ) # Отправка сообщения об ошибке

    except ValueError as e: # Перехват ошибки неверного формата
        await message.answer(
            f"❌ Ошибка: Неверный формат даты и времени. Используйте ДД.ММ.ГГГГ ЧЧ:ММ, например, 25.12.2023 15:30",
            reply_markup=kb.back_button
        ) # Отправка сообщения об ошибке
    except Exception as e: # Перехват других ошибок
        await message.answer(
            f"❌ Произошла ошибка: {str(e)}",
            reply_markup=kb.back_to_main
        ) # Отправка сообщения об ошибке

    await state.clear() # Очистка текущего состояния


@router.callback_query(F.data.startswith('select_reminder_'))
async def select_reminder(callback: CallbackQuery):
    task_id, reminder_id = map(int, callback.data.split('_')[2:4]) # Извлечение ID задачи и напоминания
    task = await get_task_by_id(task_id) # Получение задачи по ID
    if task and task.reminders: # Проверка наличия задачи и напоминаний
        reminder = next((r for r in task.reminders if r.id == reminder_id and r.is_active), None) # Поиск активного напоминания
        if reminder: # Проверка существования напоминания
            reminder_time = reminder.remind_time.strftime("%d.%m.%Y %H:%M") # Форматирование времени напоминания
            await callback.message.edit_text(
                f"📅 Напоминание: {task.task}\nВремя: {reminder_time}",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(text="✏️ Изменить",
                                                 callback_data=f"edit_reminder_{task_id}_{reminder_id}"),
                            InlineKeyboardButton(text="❌ Удалить", callback_data=f"remove_reminder_{reminder_id}")
                        ],
                        [InlineKeyboardButton(text="⬅ Назад", callback_data="view_reminders")]
                    ]
                )
            ) # Редактирование сообщения с информацией о напоминании и опциями
        else: # Обработка отсутствия напоминания
            await callback.message.edit_text("❌ Напоминание не найдено", reply_markup=kb.back_button) # Редактирование сообщения об ошибке
    else: # Обработка отсутствия задачи или напоминаний
        await callback.message.edit_text("❌ Задача или напоминание не найдены", reply=kb.back_button) # Редактирование сообщения об ошибке
    await callback.answer() # Подтверждение обработки callback-запроса


@router.callback_query(F.data == 'add_reminder')
async def add_reminder(callback: CallbackQuery, state: FSMContext):
    tasks = await rq.get_tasks(callback.from_user.id) # Получение списка задач
    if not tasks: # Проверка наличия задач
        await callback.message.edit_text(
            "📭 У вас нет задач. Сначала добавьте задачу через 'Добавить задачу'.",
            reply_markup=kb.back_button
        ) # Редактирование сообщения с предложением добавить задачу
        await callback.answer() # Подтверждение обработки callback-запроса
        return # Завершение выполнения функции

    await callback.message.edit_text(
        "Выберите задачу для установки напоминания:",
        reply_markup=await kb.remind_tasks(callback.from_user.id, page=0)
    ) # Редактирование сообщения с выбором задачи для напоминания
    await callback.answer() # Подтверждение обработки callback-запроса