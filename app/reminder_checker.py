import asyncio
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.requests import get_active_reminders, deactivate_reminder, get_user_by_task_id, get_task_by_id

async def check_reminders(bot):
    while True:
        try:
            reminders = await get_active_reminders()
            now = datetime.now()

            for reminder in reminders:
                if reminder.remind_time <= now:
                    user_id = await get_user_by_task_id(reminder.task_id)
                    if user_id is None:
                        # User or task not found, deactivate reminder and skip
                        await deactivate_reminder(reminder.id)
                        print(f"Deactivated reminder {reminder.id} for missing user or task")
                        continue

                    task = await get_task_by_id(reminder.task_id)
                    if not task:
                        # Task deleted, deactivate reminder
                        await deactivate_reminder(reminder.id)
                        print(f"Deactivated reminder {reminder.id} for missing task")
                        continue

                    # Send reminder message
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🔔 Напоминание: {task.task}"
                    )

                    # Create inline keyboard for delete/keep options
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text="Удалить задачу",
                                callback_data=f"delete_after_reminder_{task.id}"
                            ),
                            InlineKeyboardButton(
                                text="Оставить",
                                callback_data=f"keep_after_reminder_{task.id}"
                            )
                        ]
                    ])

                    # Send follow-up message with options
                    await bot.send_message(
                        chat_id=user_id,
                        text="Хотите удалить эту задачу?",
                        reply_markup=keyboard
                    )

                    # Deactivate the reminder
                    await deactivate_reminder(reminder.id)

            await asyncio.sleep(30)  # Check every 30 seconds

        except Exception as e:
            print(f"Ошибка в проверщике: {e}")