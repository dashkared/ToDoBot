from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Filter, Command
from aiogram.fsm.context import FSMContext
from app.states import Newsletter
from app.database.requests import get_users
admin = Router()

class Admin(Filter):
    async def __call__(self, message: Message):
        return message.from_user.id in [1896437987,87457758,850715316]

@admin.message(Admin(), Command('new'))
async def newsletter(message:Message, state:FSMContext):
    await state.set_state(Newsletter.message)
    await message.answer('Введите сообщение для рассылки')

@admin.message(Newsletter.message)
async def newsletter_message(message:Message, state:FSMContext):
    await  state.clear()
    await message.answer('Рассылка началась.')
    users = await get_users()
    for user in users:
        try:
            await message.send_copy()
        except Exception as e:
            print(e)
    await message.answer('Рассылка завершена.')




