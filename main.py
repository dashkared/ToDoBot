import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import logging
from dotenv import load_dotenv
from app.database.models import async_main
from app.middlewares import BlockUserMiddleware

logging.basicConfig(level=logging.INFO) # Настройка базового уровня логирования на INFO

async def main():
    load_dotenv() # Загрузка переменных окружения из файла .env
    await async_main() # Инициализация базы данных (создание таблиц)
    bot = Bot(token=os.getenv('TG_TOKEN')) # Создание экземпляра бота с токеном из переменной окружения
    dp = Dispatcher() # Создание диспетчера для обработки обновлений
    print('Бот запущен') # Вывод сообщения о запуске бота в консоль
    dp.update.outer_middleware(BlockUserMiddleware()) # Регистрация middleware для обработки случаев, когда бот заблокирован пользователем
    # Импорт обработчиков
    from app.handlers import router
    from app.admin import admin
    dp.include_router(router) # Подключение основного роутера с обработчиками команд и callback-запросов
    dp.include_router(admin) # Подключение роутера для админских функций (например, рассылки)

    # Запуск напоминаний
    from app.reminder_checker import check_reminders
    asyncio.create_task(check_reminders(bot)) # Запуск фоновой задачи для проверки и отправки напоминаний

    await dp.start_polling(bot) # Запуск поллинга для получения обновлений от Telegram

if __name__ == "__main__":
    try:
        asyncio.run(main()) # Запуск основной асинхронной функции main()
    except KeyboardInterrupt:
        print("Бот остановлен.") # Вывод сообщения об остановке бота при прерывании (Ctrl+C)