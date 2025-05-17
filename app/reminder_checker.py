import asyncio
from datetime import datetime
from app.database.requests import get_active_reminders, deactivate_reminder, get_user_by_task_id, get_task_by_id


async def check_reminders(bot):
    while True:
        try:
            reminders = await get_active_reminders()
            now = datetime.now()

            for reminder in reminders:
                if reminder.remind_time <= now:
                    user_id = await get_user_by_task_id(reminder.task_id)
                    task = await get_task_by_id(reminder.task_id)

                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🔔 Напоминание: {task.task}"
                    )
                    await deactivate_reminder(reminder.id)

            await asyncio.sleep(30)  # Проверка каждые 30 секунд

        except Exception as e:
            print(f"Ошибка в проверщике: {e}")
