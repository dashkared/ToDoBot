
        

import os
import asyncio
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
from app.handlers import router
from app.admin import admin
from app.database.models import async_main

async def main():
    load_dotenv()
    await async_main()
    print("Бот запущен!")
    bot = Bot(token=os.getenv('TG_TOKEN'))
    dp = Dispatcher()
    dp.include_router(router)
    dp.include_router(admin)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")

