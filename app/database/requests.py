from app.database.models import async_session
from app.database.models import User, Task
import datetime
from app.database.models import Reminder  # Импорт модели
from sqlalchemy import select


async def set_user(tg_id):
    async with async_session() as session:
        # Правильная проверка существования пользователя
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id))
            await session.commit()


def connection(func):
    async def inner(*args, **kwargs):
        async with async_session() as session:
            return await func(session, *args, **kwargs)

    return inner


@connection
async def get_users(session):
    result = await session.scalars(select(User.tg_id).distinct())
    return result.all()


async def get_tasks(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return []
        await session.refresh(user)  # Обновляем данные
        tasks = await session.scalars(select(Task).where(Task.user == user.id))
        return tasks.all()  # Явно возвращаем список


async def set_task(tg_id, task):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        new_task = Task(task=task, user=user.id)
        session.add(new_task)
        await session.commit()
        await session.refresh(new_task)  # Обновляем объект чтобы получить ID
        return new_task.id  # Возвращаем ID созданной задачи


async def del_task(task_id):
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            await session.delete(task)
            await session.commit()
            return True
        return False

async def update_task(task_id, new_text):
    async with async_session() as session:
        task = await session.get(Task, task_id)
        if task:
            task.task = new_text
            await session.commit()
            await session.refresh(task)  # Обновляем данные
            return True
        return False


async def set_reminder(task_id, remind_time: datetime):
    async with async_session() as session:
        session.add(Reminder(task_id=task_id, remind_time=remind_time))
        await session.commit()


async def get_user_by_task_id(task_id):
    async with async_session() as session:
        task = await session.get(Task, task_id)
        user = await session.get(User, task.user)
        return user.tg_id


async def get_active_reminders():
    async with async_session() as session:
        reminders = await session.scalars(
            select(Reminder).where(Reminder.is_active == True))
        return reminders.all()

async def deactivate_reminder(reminder_id):
    async with async_session() as session:
        reminder = await session.get(Reminder, reminder_id)
        if reminder:
            reminder.is_active = False
            await session.commit()
            return True
        return False

async def get_task_by_id(task_id):
    async with async_session() as session:
        task = await session.get(Task, task_id)
        return task
    
    
async def delete_user_data(tg_id):
    async with async_session() as session:
        # Находим пользователя
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return False
        
        # Удаляем пользователя (каскадное удаление задач и напоминаний)
        await session.delete(user)
        await session.commit()
        return True
