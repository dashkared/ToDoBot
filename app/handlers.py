import asyncio
import logging
from aiogram import F, Router
from aiogram.types import Message, CallbackQuery, reply_keyboard_remove
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from app.database.requests import set_user, del_task, set_task
from aiogram.enums import ChatAction
from app.states import TaskActions
from app.database.requests import update_task
import app.keyboards as kb
import app.database.requests as rq

router = Router()


class Register(StatesGroup):
    name = State()
    age = State()
    number = State()



@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.bot.send_chat_action(chat_id=message.from_user.id, action=ChatAction.TYPING)
    await asyncio.sleep(1)
    await rq.set_user(message.from_user.id)
    await message.answer("Добро пожаловать в ToDo Bot!", reply_markup=kb.inline_main)


@router.message(Command('register'))
async def register(message: Message, state: FSMContext):
    await state.set_state(Register.name)
    await message.answer('Введите ваше имя')


@router.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Register.age)
    await message.answer('Введите ваш возраст')


@router.message(Register.age)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(age=message.text)
    await state.set_state(Register.number)
    await message.answer('Введите ваш номер телефона', reply_markup=kb.get_number)


@router.message(Register.number, F.contact)
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number=message.contact.phone_number)
    data = await state.get_data()
    await message.answer(f'Ваше имя: {data["name"]}\nВаш возраст: {data["age"]}\nНомер: {data["number"]}')
    await state.clear()


@router.callback_query(F.data == 'my_task')
async def task(callback: CallbackQuery):
    tasks = await rq.get_tasks(callback.from_user.id)

    if not tasks:
        await callback.message.edit_text(
            "📭 Список задач пуст",
            reply_markup=kb.my_task
        )
        return await callback.answer()

    tasks_text = "📋 Ваши текущие задачи:\n\n" + "\n".join(
        f"▫️ {task.task}" for task in tasks
    )

    await callback.message.edit_text(
        f"{tasks_text}\n\nВыберите действие:",
        reply_markup=kb.my_task
    )
    await callback.answer()


@router.callback_query(F.data == 'back')
async def return_back(callback: CallbackQuery):
    await callback.message.edit_text('Выберите пункт меню', reply_markup=kb.inline_main)


# Добавление задачи
@router.callback_query(F.data == 'add')
async def add_task(callback: CallbackQuery, state: FSMContext):
    await state.set_state(TaskActions.adding)
    await callback.message.edit_text("Введите текст новой задачи:")
    await callback.answer()


@router.message(TaskActions.adding)
async def task_added(message: Message, state: FSMContext):
    await set_task(message.from_user.id, message.text)
    await message.answer("Задача добавлена!", reply_markup=kb.inline_main)
    await state.clear()


# Удаление задачи
@router.callback_query(F.data == 'delete')
async def delete_task_menu(callback: CallbackQuery):
    tasks_markup = await kb.delete_tasks(callback.from_user.id)
    await callback.message.edit_text("Выберите задачу для удаления:", reply_markup=tasks_markup)
    await callback.answer()


@router.callback_query(F.data.startswith('delete_'))
async def delete_selected_task(callback: CallbackQuery):
    task_id = int(callback.data.split('_')[1])
    success = await del_task(task_id)
    if success:
        await callback.message.edit_text("✅ Задача удалена!", reply_markup=kb.inline_main)
    else:
        await callback.message.edit_text("❌ Задача не найдена")
    await callback.answer()


# Изменение задачи
@router.callback_query(F.data == 'change')
async def change_task_menu(callback: CallbackQuery):
    tasks_markup = await kb.edit_tasks(callback.from_user.id)
    await callback.message.edit_text("Выберите задачу для изменения:", reply_markup=tasks_markup)
    await callback.answer()


@router.callback_query(F.data.startswith('edit_'))
async def select_task_to_edit(callback: CallbackQuery, state: FSMContext):
    task_id = int(callback.data.split('_')[1])
    await state.update_data(task_id=task_id)
    await state.set_state(TaskActions.new_text)
    await callback.message.edit_text("Введите новый текст задачи:")
    await callback.answer()


@router.message(TaskActions.new_text)
async def save_updated_task(message: Message, state: FSMContext):
    data = await state.get_data()
    success = await update_task(data['task_id'], message.text)
    if success:
        await message.answer("✅ Задача изменена!", reply_markup=kb.inline_main)
    else:
        await message.answer("❌ Ошибка: задача не найдена")
    await state.clear()


