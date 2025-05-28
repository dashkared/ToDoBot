import asyncio
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.database.requests import get_active_reminders, deactivate_reminder, get_user_by_task_id, get_task_by_id

async def check_reminders(bot):
    while True: # Бесконечный цикл для периодической проверки напоминаний
        try: # Начало блока обработки ошибок
            reminders = await get_active_reminders() # Получение списка активных напоминаний
            now = datetime.now() # Получение текущего времени

            for reminder in reminders: # Перебор всех активных напоминаний
                if reminder.remind_time <= now: # Проверка, наступило ли время напоминания
                    user_id = await get_user_by_task_id(reminder.task_id) # Получение Telegram ID пользователя по ID задачи
                    if user_id is None: # Проверка, найден ли пользователь
                        await deactivate_reminder(reminder.id) # Деактивация напоминания, если пользователь не найден
                        print(f"Deactivated reminder {reminder.id} for missing user or task") # Вывод сообщения о деактивации
                        continue # Переход к следующему напоминанию

                    task = await get_task_by_id(reminder.task_id) # Получение задачи по её ID
                    if not task: # Проверка, существует ли задача
                        await deactivate_reminder(reminder.id) # Деактивация напоминания, если задача не найдена
                        print(f"Deactivated reminder {reminder.id} for missing task") # Вывод сообщения о деактивации
                        continue # Переход к следующему напоминанию

                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🔔 Напоминание: {task.task}"
                    ) # Отправка сообщения с текстом напоминания пользователю

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
                    ]) # Создание инлайн-клавиатуры с кнопками для удаления или оставления задачи

                    await bot.send_message(
                        chat_id=user_id,
                        text="Хотите удалить эту задачу?",
                        reply_markup=keyboard
                    ) # Отправка сообщения с вопросом и клавиатурой

                    await deactivate_reminder(reminder.id) # Деактивация напоминания после отправки

            await asyncio.sleep(30) # Пауза в 30 секунд перед следующей проверкой

        except Exception as e: # Перехват любых ошибок
            print(f"Ошибка в проверщике: {e}") # Вывод ошибки в консоль