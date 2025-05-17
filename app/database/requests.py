from app.database.models import async_session
from app.database.models import User, Task
from sqlalchemy import select
from sqlalchemy import delete


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
        tasks = await session.scalars(select(Task).where(Task.user == user.id))
        return tasks


async def set_task(tg_id, task):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        session.add(Task(task=task, user=user.id))
        await session.commit()


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
            return True
        return False