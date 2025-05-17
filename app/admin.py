from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.states import Newsletter
from app.database.requests import get_users

admin = Router()
ADMIN_IDS = [1896437987, 874577586, 850715316, 380854374]  # Проверьте ID!

@admin.message(Command('new'), F.from_user.id.in_(ADMIN_IDS))
async def newsletter(message: Message, state: FSMContext):
    await state.set_state(Newsletter.message)
    await message.answer('Введите сообщение для рассылки')

'''@admin.message(Newsletter.message, F.from_user.id.in_(ADMIN_IDS))
async def newsletter_message(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Рассылка началась...')
    
    users = await get_users()
    successful = 0
    
    for user in users:
        try:
            await message.copy_to(chat_id=user.tg_id)  # Используем tg_id
            successful += 1
        except Exception as e:
            print(f"Ошибка: {e}")
    
    await message.answer(f"Отправлено: {successful} пользователям")'''


@admin.message(Newsletter.message, F.from_user.id.in_(ADMIN_IDS))
async def newsletter_message(message: Message, state: FSMContext):
    await state.clear()
    await message.answer('Рассылка началась...')

    users = await get_users()
    unique_users = list(set(users))  # Дополнительная защита от дубликатов
    successful = 0

    for user_id in unique_users:
        try:
            await message.copy_to(chat_id=user_id)
            successful += 1
        except Exception as e:
            print(f"Ошибка: {e}")

    await message.answer(f"Отправлено: {successful} пользователям")