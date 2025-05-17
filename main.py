import os
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

async def main():
    load_dotenv()

    bot = Bot(token=os.getenv('TG_TOKEN'))
    dp = Dispatcher()
    print('Бот запущен')
    # Импорт обработчиков
    from app.handlers import router
    from app.admin import admin
    dp.include_router(router)
    dp.include_router(admin)

    # Запуск напоминаний
    from app.reminder_checker import check_reminders
    asyncio.create_task(check_reminders(bot))

    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")