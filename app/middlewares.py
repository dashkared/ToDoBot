from aiogram import BaseMiddleware
from aiogram.types import Update
from aiogram.exceptions import TelegramForbiddenError
import logging

logger = logging.getLogger(__name__) # Создание логгера для записи событий текущего модуля

class BlockUserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data):
        try: # Начало блока обработки ошибок
            return await handler(event, data) # Вызов следующего обработчика в цепочке с передачей события и данных
        except TelegramForbiddenError as e: # Перехват ошибки, возникающей, когда бот заблокирован пользователем
            user_id = event.from_user.id if event.from_user else "unknown" # Получение ID пользователя или установка "unknown" если пользователь не определён
            logger.warning(f"User {user_id} has blocked the bot: {e}") # Запись предупреждения в лог с информацией о блокировке
            return  # Прекращение обработки обновления для заблокированного пользователя