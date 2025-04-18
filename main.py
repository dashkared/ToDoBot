import os
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from app.handlers import router
from app.database.models import async_main


# Функция запуска бота
async def main():
    load_dotenv()
    await async_main()
    print("Бот запущен!")
    bot = Bot(token=os.getenv('TG_TOKEN'))
    dp = Dispatcher()
    dp.include_router(router)
    # Запускаем диспетчер
    await dp.start_polling(bot)

# Запуск бота с обработкой ошибок
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")

