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


import app.keyboards as kb
import app.database.requests as rq
router = Router()


class Register(StatesGroup):
    name = State()
    age = State()
    number = State()

# Хэндлер для команды /start
@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.bot.send_chat_action(chat_id=message.from_user.id,action=ChatAction.TYPING)
    await asyncio.sleep(1)
    await rq.set_user(message.from_user.id)
    await message.answer("Добро пожаловать в ToDo Bot!", reply_markup=kb.inline_main)


    
@router.message(Command('register'))
async def register(message: Message, state: FSMContext):
    await state.set_state(Register.name)
    await message.answer('Введите ваше имя')
    
@router.message(Register.name)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(name = message.text)
    await state.set_state(Register.age)
    await message.answer('Введите ваш возраст')
    
@router.message(Register.age)
async def register_name(message: Message, state: FSMContext):
    await state.update_data(age = message.text)
    await state.set_state(Register.number)
    await message.answer('Введите ваш номер телефона', reply_markup=kb.get_number)

@router.message(Register.number, F.contact)
async def register_number(message: Message, state: FSMContext):
    await state.update_data(number = message.contact.phone_number)
    data = await state.get_data()
    await message.answer(f'Ваше имя: {data["name"]}\nВаш возраст: {data["age"]}\nНомер: {data["number"]}')
    await state.clear()

@router.callback_query(F.data == 'my_task')
async def task(callback: CallbackQuery):
    await callback.answer('Вы выбрали Мои задачи')
    await callback.message.edit_text('Выберите пункт меню', reply_markup= kb.my_task)

@router.callback_query(F.data == 'back')
async def return_back(callback: CallbackQuery):
    await callback.message.edit_text('Выберите пункт меню', reply_markup=kb.inline_main)

