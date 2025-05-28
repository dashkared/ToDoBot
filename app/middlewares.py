from aiogram import BaseMiddleware
from aiogram.types import Update
from aiogram.exceptions import TelegramForbiddenError
import logging

logger = logging.getLogger(__name__)

class BlockUserMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data):
        try:
            return await handler(event, data)
        except TelegramForbiddenError as e:
            user_id = event.from_user.id if event.from_user else "unknown"
            logger.warning(f"User {user_id} has blocked the bot: {e}")
            return  # Skip processing the update