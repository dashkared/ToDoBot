from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from app.states import Newsletter
from app.database.requests import get_users

admin = Router() # Создание роутера для обработки административных команд
ADMIN_IDS = [1896437987, 874577586, 850715316, 380854374] # Список Telegram ID администраторов

@admin.message(Command('newsletter'), F.from_user.id.in_(ADMIN_IDS))
async def newsletter(message: Message, state: FSMContext): # Обработчик команды /newsletter для администраторов
    await state.set_state(Newsletter.message) # Установка состояния для ввода сообщения рассылки
    await message.answer('Введите сообщение для рассылки') # Отправка запроса на ввод сообщения

@admin.message(Newsletter.message, F.from_user.id.in_(ADMIN_IDS))
async def newsletter_message(message: Message, state: FSMContext): # Обработчик ввода сообщения рассылки
    await state.clear() # Очистка текущего состояния
    await message.answer('Рассылка началась...') # Отправка сообщения о начале рассылки

    users = await get_users() # Получение списка Telegram ID пользователей
    unique_users = list(set(users)) # Удаление дубликатов пользователей
    successful = 0 # Счётчик успешно отправленных сообщений

    for user_id in unique_users: # Перебор всех уникальных пользователей
        try: # Начало блока обработки ошибок
            await message.copy_to(chat_id=user_id) # Копирование сообщения пользователю
            successful += 1 # Увеличение счётчика успешных отправок
        except Exception as e: # Перехват любых ошибок
            print(f"Ошибка: {e}") # Вывод ошибки в консоль

    await message.answer(f"Отправлено: {successful} пользователям") # Отправка итогового сообщения с количеством успешных отправок