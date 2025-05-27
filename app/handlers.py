import asyncio
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
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
from datetime import datetime
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

router = Router()


class Register(StatesGroup):
    name = State()
    age = State()
    number = State()


@router.message(Command("start"))
async def start_cmd(message: Message):
    await set_user(message.from_user.id)  # Ensure user is created in DB
    await message.bot.send_chat_action(chat_id=message.from_user.id, action=ChatAction.TYPING)
    await asyncio.sleep(1)
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
    )
    await message.answer(welcome_text, reply_markup=kb.back_to_main)


@router.message(Command("menu"))
async def menu_cmd(message: Message):
    await message.answer("Выберите пункт меню:", reply_markup=kb.inline_main)


@router.message(Command("tasks"))
async def tasks_cmd(message: Message):
    tasks = await rq.get_tasks(message.from_user.id)
    keyboard = await kb.my_task_kb(message.from_user.id)

    if not tasks:
        await message.answer(
            "📭 Список задач пуст",
            reply_markup=keyboard
        )
        return

    tasks_text = "📋 Ваши текущие задачи:\n\n" + "\n".join(f"▫️ {task.task}" for task in tasks)
    await message.answer(
        f"{tasks_text}\n\nВыберите действие:",
        reply_markup=keyboard
    )

'''@router.message(Command('register'))
async def register(message: Message, state: FSMContext):
    await state.set_state(Register.name)
    await message.answer('Введите ваше имя', reply_markup=kb.back_to_main)

@router.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.age)
    await message.answer('Введите ваш возраст', reply_markup=kb.back_to_main)

@router.message(Register.age)
async def register_age(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Register.number)
    await message.answer('Введите ваш номер телефона', reply_markup=kb.get_number)

@router.message(Register.number, F.contact)
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number=message.contact.phone_number)
    data = await state.get_data()
    await message.answer(f'Ваше имя: {data["name"]}\nВаш возраст: {data["age"]}\nНомер: {data["number"]}',
                         reply_markup=kb.back_to_main)
    await state.clear()'''

@router.message(F.text == "Мои задачи")
async def show_tasks(message: Message):
    tasks = await rq.get_tasks(message.from_user.id)
    keyboard = await kb.my_task_kb(message.from_user.id)

    if not tasks:
        await message.answer(
            "📭 Список задач пуст",
            reply_markup=keyboard
        )
        return

    tasks_text = "📋 Ваши текущие задачи:\n\n" + "\n".join(f"▫️ {task.task}" for task in tasks)
    await message.answer(
        f"{tasks_text}\n\nВыберите действие:",
        reply_markup=keyboard
    )


@router.callback_query(F.data == 'my_task')
async def task(callback: CallbackQuery):
    tasks = await rq.get_tasks(callback.from_user.id)
    keyboard = await kb.my_task_kb(callback.from_user.id)

    if not tasks:
        await callback.message.edit_text(
            "📭 Список задач пуст",
            reply_markup=keyboard
        )
        return await callback.answer()

    tasks_text = "📋 Ваши текущие задачи:\n\n" + "\n".join(f"▫️ {task.task}" for task in tasks)
    await callback.message.edit_text(
        f"{tasks_text}\n\nВыберите действие:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == 'back')
async def return_back(callback: CallbackQuery, state: FSMContext):
    current_state = await state.get_state()

    if current_state in [TaskActions.adding, TaskActions.reminder_time, TaskActions.edit_reminder]:
        await state.clear()
        tasks = await rq.get_tasks(callback.from_user.id)
        keyboard = await kb.my_task_kb(callback.from_user.id)

        text = "📭 Список задач пуст" if not tasks else "📋 Ваши текущие задачи:\n\n" + "\n".join(
            f"▫️ {task.task}" for task in tasks)
        await callback.message.edit_text(
            f"{text}\n\nВыберите действие:",
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text('Выберите пункт меню', reply_markup=kb.inline_main)

    await callback.answer()


@router.message(F.text == "Главное меню")
async def main_menu(message: Message):
    await message.answer("Выберите пункт меню:", reply_markup=kb.inline_main)


@router.callback_query(F.data == 'ai_req')
async def ai_generating(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        'Напишите запрос для нейросети:',
        reply_markup=kb.ai_cancel
    )
    await state.set_state(Gen.wait)
    await callback.answer()


@router.message(Gen.wait)
async def process_ai_request(message: Message, state: FSMContext):
    await message.answer("⏳ Ваш запрос обрабатывается...", reply_markup=kb.back_to_main)

    try:
        response = await ai_generate(message.text)
        await message.answer(text=response,
                             reply_markup=kb.after_ai_response,
                             parse_mode='Markdown'
                             )
    except Exception as e:
        await message.answer(
            f"⚠️ Произошла ошибка: {str(e)}",
            reply_markup=kb.back_to_main
        )

    await state.clear()


@router.message(Command("del"))
async def clear_data(message: Message, state: FSMContext):
    tasks = await rq.get_tasks(message.from_user.id)
    if not tasks:
        await message.answer("❌ У вас нет задач для удаления", reply_markup=kb.back_to_main)
        return

    await state.set_state(TaskActions.deleting)
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
    )


@router.callback_query(F.data == "confirm_delete")
async def confirm_delete_tasks(callback: CallbackQuery, state: FSMContext):
    success = await rq.delete_user_data(callback.from_user.id)
    await state.clear()
    if success:
        await callback.message.edit_text(
            "✅ Все ваши задачи удалены!",
            reply_markup=kb.inline_main
        )
    else:
        await callback.message.edit_text(
            "❌ У вас нет задач для удаления",
            reply_markup=kb.inline_main
        )
    await callback.answer()


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete_tasks(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "✅ Удаление отменено",
        reply_markup=kb.inline_main
    )
    await callback.answer()


@router.callback_query(F.data == 'add')
async def add_task(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskActions.adding)
    await callback.message.edit_text(
        "Введите текст новой задачи:",
        reply_markup=kb.back_button
    )
    await callback.answer()


@router.message(TaskActions.adding)
async def task_added(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        tasks = await rq.get_tasks(message.from_user.id)
        keyboard = await kb.my_task_kb(message.from_user.id)
        text = "📭 Список задач пуст" if not tasks else "📋 Ваши текущие задачи:\n\n" + "\n".join(
            f"▫️ {task.task}" for task in tasks)
        await message.answer(
            f"{text}\n\nВыберите действие:",
            reply_markup=keyboard
        )
        return

    try:
        task_id = await set_task(message.from_user.id, message.text)
        await state.update_data(new_task_id=task_id)
        await message.answer(
            "✅ Задача добавлена! Хотите установить напоминание?",
            reply_markup=kb.confirm_reminder
        )
        await state.set_state(TaskActions.ask_reminder)
    except Exception as e:
        await message.answer(
            f"❌ Не удалось добавить задачу: {str(e)}",
            reply_markup=kb.back_to_main
        )
        await state.clear()


@router.callback_query(F.data == "remind_yes", TaskActions.ask_reminder)
async def confirm_reminder(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    task_id = data.get('new_task_id')

    await state.update_data(task_id=task_id)
    await state.set_state(TaskActions.reminder_time)

    await callback.message.edit_text(
        "Введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ\nПример: 28.05.2025 15:30",
        reply_markup=kb.back_button
    )
    await callback.answer()


@router.callback_query(F.data == "remind_no", TaskActions.ask_reminder)
async def cancel_reminder(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "✅ Задача сохранена без напоминания!",
        reply_markup=kb.inline_main
    )
    await callback.answer()


@router.callback_query(F.data.regexp(r'^delete_(0|prev_\d+|next_\d+)$'))
async def delete_task_menu(callback: CallbackQuery):
    if callback.data == 'delete_0':
        page = 0
    elif callback.data.startswith('delete_prev_') or callback.data.startswith('delete_next_'):
        page = int(callback.data.split('_')[2])
        if callback.data.startswith('delete_prev_') and page == 0:
            await callback.answer("Это первая страница!", show_alert=False)
            return
        page = max(0, page - 1) if callback.data.startswith('delete_prev_') else page + 1
    else:
        page = int(callback.data.split('_')[1])
    tasks_markup = await kb.delete_tasks(callback.from_user.id, page)
    await callback.message.edit_text("Выберите задачу для удаления:", reply_markup=tasks_markup)
    await callback.answer()


@router.callback_query(F.data.regexp(r'^delete_\d+$'))
async def delete_selected_task(callback: CallbackQuery):
    task_id = int(callback.data.split('_')[1])
    success = await del_task(task_id)
    if success:
        new_kb = await kb.my_task_kb(callback.from_user.id)
        await callback.message.edit_text("✅ Задача удалена!", reply_markup=new_kb)
    else:
        await callback.message.edit_text("❌ Задача не найдена", reply_markup=kb.back_button)
    await callback.answer()


@router.callback_query(F.data.regexp(r'^change_(0|prev_\d+|next_\d+)$'))
async def change_task_menu(callback: CallbackQuery):
    if callback.data == 'change_0':
        page = 0
    elif callback.data.startswith('change_prev_') or callback.data.startswith('change_next_'):
        page = int(callback.data.split('_')[2])
        if callback.data.startswith('change_prev_') and page == 0:
            await callback.answer("Это первая страница!", show_alert=False)
            return
        page = max(0, page - 1) if callback.data.startswith('change_prev_') else page + 1
    else:
        page = int(callback.data.split('_')[1])
    tasks_markup = await kb.edit_tasks(callback.from_user.id, page)
    await callback.message.edit_text("Выберите задачу для изменения:", reply_markup=tasks_markup)
    await callback.answer()


@router.callback_query(F.data.startswith('change_'))
async def select_task_to_edit(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split('_')[1])
    await state.update_data(task_id=task_id)
    await state.set_state(TaskActions.new_text)
    await callback.message.edit_text("Введите новый текст задачи:", reply_markup=kb.back_button)
    await callback.answer()


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
                                     parse_mode='HTML')


@router.callback_query(F.data == 'feedback')
async def feedback(callback: CallbackQuery):
    await callback.message.edit_text('📋Пройдите опрос, связанный с нашим ботом'
                                     '\nНам важно ваше мнение🙏'
                                     '\n https://forms.gle/gf5xcFqHR8kGkh9H7', reply_markup=kb.back_button)


@router.message(TaskActions.new_text)
async def save_updated_task(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get('task_id')
    new_text = message.text
    if not task_id:
        await message.answer("❌ Ошибка: задача не найдена", reply_markup=kb.back_to_main)
        await state.clear()
        return

    success = await update_task(task_id, new_text)
    if success:
        new_kb = await kb.my_task_kb(message.from_user.id)
        await message.answer("✅ Задача изменена!", reply_markup=new_kb)
    else:
        await message.answer("❌ Ошибка: задача не найдена", reply_markup=kb.back_to_main)
    await state.clear()


@router.callback_query(F.data.regexp(r'^remind_(0|prev_\d+|next_\d+)$'))
async def remind_task_menu(callback: CallbackQuery):
    if callback.data == 'remind_0':
        page = 0
    elif callback.data.startswith('remind_prev_') or callback.data.startswith('remind_next_'):
        page = int(callback.data.split('_')[2])
        if callback.data.startswith('remind_prev_') and page == 0:
            await callback.answer("Это первая страница!", show_alert=False)
            return
        page = max(0, page - 1) if callback.data.startswith('remind_prev_') else page + 1
    else:
        page = int(callback.data.split('_')[1])
    tasks_markup = await kb.remind_tasks(callback.from_user.id, page)
    await callback.message.edit_text("Выберите задачу для напоминания:", reply_markup=tasks_markup)
    await callback.answer()


@router.callback_query(F.data.regexp(r'^remind_\d+$'))
async def select_task_to_remind(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split('_')[1])
    await state.update_data(task_id=task_id)
    await state.set_state(TaskActions.reminder_time)
    await callback.message.edit_text(
        "Введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ\nПример: 28.05.2025 15:30",
        reply_markup=kb.back_button
    )
    await callback.answer()


@router.callback_query(F.data.startswith('delete_after_reminder_') | F.data.startswith('keep_after_reminder_'))
async def handle_reminder_action(callback: CallbackQuery):
    action, task_id = callback.data.split('_')[0], int(callback.data.split('_')[3])

    if action == 'delete':
        success = await del_task(task_id)
        if success:
            await callback.message.edit_text("✅ Задача удалена!", reply_markup=kb.back_button)
            await callback.message.answer("Выберите действие:", reply_markup=kb.back_to_main)
        else:
            await callback.message.edit_text("❌ Задача не найдена", reply_markup=kb.back_button)
            await callback.message.answer("Выберите действие:", reply_markup=kb.back_to_main)
    else:  # keep
        await callback.message.edit_text("✅ Задача оставлена в списке.", reply_markup=kb.back_button)
        await callback.message.answer("Выберите действие:", reply_markup=kb.back_to_main)

    await callback.answer()


@router.message(TaskActions.reminder_time)
async def save_reminder(message: Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        tasks = await rq.get_tasks(message.from_user.id)
        keyboard = await kb.my_task_kb(message.from_user.id)
        text = "📭 Список задач пуст" if not tasks else "📋 Ваши текущие задачи:\n\n" + "\n".join(
            f"▫️ {task.task}" for task in tasks)
        await message.answer(
            f"{text}\n\nВыберите действие:",
            reply_markup=keyboard
        )
        return

    if validate_date_time(message.text):
        try:
            remind_time = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        except ValueError:
            await message.answer("❌ Неверный формат! Используйте ДД.ММ.ГГГГ ЧЧ:ММ, например, 28.05.2025 15:30",
                                 reply_markup=kb.back_button)
            return

        data = await state.get_data()
        task_id = data.get('task_id')

        await rq.set_reminder(task_id, remind_time)
        await message.answer(
            f"⏰ Напоминание установлено на {remind_time.strftime('%d.%m.%Y %H:%M')}!",
            reply_markup=kb.inline_main
        )
        await state.clear()
    else:
        await message.answer("❌ Неверный формат или время в прошлом! Используйте ДД.ММ.ГГГГ ЧЧ:ММ, например,"
                             "28.05.2025 15:30", reply_markup=kb.back_button)


def validate_date_time(input_str):
    try:
        input_str = input_str.strip()
        date_str, time_str = input_str.split()
        input_datetime = datetime.strptime(f"{date_str} {time_str}", "%d.%m.%Y %H:%M")
        current_datetime = datetime.now()
        if input_datetime <= current_datetime:
            return False
        return True
    except ValueError:
        return False


@router.callback_query(F.data == 'view_reminders')
async def view_reminders(callback: CallbackQuery):
    keyboard = await kb.manage_reminders(callback.from_user.id)
    await callback.message.edit_text("📅 Активные напоминания:", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.regexp(r'^reminder_(prev|next)_(\d+)$'))
async def paginate_reminders(callback: CallbackQuery):
    try:
        action, current_page = callback.data.split('_')[1], int(callback.data.split('_')[2])
        tasks = await rq.get_tasks(callback.from_user.id)
        tasks_with_reminders = [task for task in tasks if task.reminders and any(r.is_active for r in task.reminders)]
        total_pages = max(1, (len(tasks_with_reminders) + kb.TASKS_PER_PAGE - 1) // kb.TASKS_PER_PAGE)

        new_page = current_page - 1 if action == "prev" else current_page + 1

        if action == "prev" and current_page == 0:
            await callback.answer("Это первая страница!", show_alert=True)
            return

        if action == "next" and current_page >= total_pages - 1:
            await callback.answer(
                "У вас пока нет нужного количества задач для перехода на следующую страницу",
                show_alert=True
            )
            return

        new_page = max(0, new_page)
        keyboard = await kb.manage_reminders(callback.from_user.id, new_page)
        if keyboard != callback.message.reply_markup:
            await callback.message.edit_reply_markup(reply_markup=keyboard)
        await callback.answer()

    except ValueError as e:
        await callback.answer(f"Ошибка обработки страницы: {str(e)}", show_alert=True)
    except Exception as e:
        await callback.answer(f"Произошла ошибка: {str(e)}", show_alert=True)


@router.callback_query(F.data.startswith('remove_reminder_'))
async def remove_reminder(callback: CallbackQuery):
    task_id = int(callback.data.split('_')[2])
    success = await rq.deactivate_reminder_by_task(task_id)

    if success:
        keyboard = await kb.manage_reminders(callback.from_user.id)
        await callback.message.edit_text("📅 Активные напоминания:", reply_markup=keyboard)
        await callback.answer("✅ Напоминание удалено!")
    else:
        await callback.answer("❌ Напоминание не найдено", show_alert=True)


@router.callback_query(F.data.startswith('edit_reminder_'))
async def edit_reminder(callback: CallbackQuery, state: FSMContext):
    try:
        task_id = int(callback.data.split('_')[-1])
        task = await get_task_by_id(task_id)
        if not task:
            await callback.message.edit_text("❌ Задача не найдена", reply_markup=kb.back_button)
            await callback.answer("Задача не найдена", show_alert=True)
            return

        active_reminders = [r for r in task.reminders if r.is_active] if task.reminders else []

        if not active_reminders:
            await callback.message.edit_text(
                "❌ У этой задачи нет активных напоминаний. Хотите создать новое?",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Создать напоминание", callback_data=f"remind_{task_id}")],
                        [InlineKeyboardButton(text="Назад", callback_data="view_reminders")]
                    ]
                )
            )
            await callback.answer("Нет активных напоминаний", show_alert=True)
            return

        await state.update_data(task_id=task_id)
        await state.set_state(TaskActions.edit_reminder)

        current_time = active_reminders[0].remind_time.strftime("%d.%m.%Y %H:%M")
        await callback.message.edit_text(
            f"✏️ Текущее время напоминания: {current_time}\n"
            "Введите новое время в формате ДД.ММ.ГГГГ ЧЧ:ММ (например, 25.12.2023 15:30):",
            reply_markup=kb.back_button
        )
        await callback.answer()

    except ValueError:
        await callback.message.edit_text("❌ Ошибка: Неверный формат идентификатора задачи", reply_markup=kb.back_button)
        await callback.answer("Ошибка обработки запроса", show_alert=True)
    except Exception as e:
        await callback.message.edit_text("❌ Произошла ошибка при попытке редактирования", reply_markup=kb.back_button)
        await callback.answer(f"Ошибка: {str(e)}", show_alert=True)


@router.message(TaskActions.edit_reminder)
async def save_updated_reminder(message: Message, state: FSMContext):
    data = await state.get_data()
    task_id = data.get('task_id')

    if not task_id:
        await message.answer("❌ Ошибка: задача не найдена", reply_markup=kb.back_to_main)
        await state.clear()
        return

    if message.text == "Назад":
        await state.clear()
        tasks = await rq.get_tasks(message.from_user.id)
        keyboard = await kb.my_task_kb(message.from_user.id)
        text = "📭 Список задач пуст" if not tasks else "📋 Ваши текущие задачи:\n\n" + "\n".join(
            f"▫️ {task.task}" for task in tasks)
        await message.answer(
            f"{text}\n\nВыберите действие:",
            reply_markup=keyboard
        )
        return

    try:
        if not validate_date_time(message.text):
            await message.answer(
                "❌ Неверный формат или время в прошлом! Используйте ДД.ММ.ГГГГ ЧЧ:ММ, например, 25.12.2023 15:30",
                reply_markup=kb.back_button
            )
            return

        new_time = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
        success = await rq.update_reminder_time(task_id, new_time)

        if success:
            await message.answer(
                f"✅ Напоминание обновлено на {new_time.strftime('%d.%m.%Y %H:%M')}!",
                reply_markup=kb.inline_main
            )
        else:
            await rq.set_reminder(task_id, new_time)
            await message.answer(
                f"✅ Новое напоминание установлено на {new_time.strftime('%d.%m.%Y %H:%M')}!",
                reply_markup=kb.inline_main
            )

    except ValueError as e:
        await message.answer(
            f"❌ Ошибка: Неверный формат даты и времени. Используйте ДД.ММ.ГГГГ ЧЧ:ММ, например, 25.12.2023 15:30",
            reply_markup=kb.back_button
        )
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка: {str(e)}",
            reply_markup=kb.back_to_main
        )

    await state.clear()


@router.callback_query(F.data.startswith('select_reminder_'))
async def select_reminder(callback: CallbackQuery):
    task_id = int(callback.data.split('_')[2])
    task = await get_task_by_id(task_id)
    if task and task.reminders and any(r.is_active for r in task.reminders):
        reminder_time = task.reminders[0].remind_time.strftime("%d.%m.%Y %H:%M")
        await callback.message.edit_text(
            f"📅 Напоминание: {task.task}\nВремя: {reminder_time}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit_reminder_{task_id}"),
                        InlineKeyboardButton(text="❌ Удалить", callback_data=f"remove_reminder_{task_id}")
                    ],
                    [InlineKeyboardButton(text="⬅️ Назад", callback_data="view_reminders")]
                ]
            )
        )
    else:
        await callback.message.edit_text("❌ Напоминание не найдено", reply_markup=kb.back_button)
    await callback.answer()


@router.callback_query(F.data == 'add_reminder')
async def add_reminder(callback: CallbackQuery, state: FSMContext):
    tasks = await rq.get_tasks(callback.from_user.id)
    if not tasks:
        await callback.message.edit_text(
            "📭 У вас нет задач. Сначала добавьте задачу через 'Добавить задачу'.",
            reply_markup=kb.back_button
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "Выберите задачу для установки напоминания:",
        reply_markup=await kb.remind_tasks(callback.from_user.id, page=0)
    )
    await callback.answer()