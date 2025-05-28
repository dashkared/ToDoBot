from app.database.models import async_session, User, Task, Reminder
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def set_user(tg_id):
    async with async_session() as session: # Создание асинхронной сессии для работы с базой данных
        user = await session.scalar(select(User).where(User.tg_id == tg_id)) # Поиск пользователя в базе данных по Telegram ID
        if not user: # Проверка, существует ли пользователь
            session.add(User(tg_id=tg_id)) # Добавление нового пользователя в сессию
            await session.commit() # Фиксация изменений в базе данных

def connection(func):
    async def inner(*args, **kwargs): # Определение внутренней функции-обёртки
        async with async_session() as session: # Создание асинхронной сессии
            return await func(session, *args, **kwargs) # Вызов декорируемой функции с передачей сессии и аргументов
    return inner # Возврат обёртки

@connection
async def get_users(session): # Функция для получения уникальных Telegram ID пользователей
    result = await session.scalars(select(User.tg_id).distinct()) # Выполнение запроса на выборку уникальных Telegram ID
    return result.all() # Возврат списка всех Telegram ID

async def get_tasks(tg_id):
    async with async_session() as session: # Создание асинхронной сессии
        user = await session.scalar(select(User).where(User.tg_id == tg_id)) # Поиск пользователя по Telegram ID
        if not user: # Проверка, существует ли пользователь
            return [] # Возврат пустого списка, если пользователь не найден
        await session.refresh(user) # Обновление данных пользователя из базы
        tasks = await session.scalars(
            select(Task)
            .where(Task.user == user.id)
            .options(selectinload(Task.reminders))) # Выполнение запроса на выборку задач пользователя с подгрузкой связанных напоминаний
        return tasks.all() # Возврат списка всех задач

async def set_task(tg_id, task):
    async with async_session() as session: # Создание асинхронной сессии
        user = await session.scalar(select(User).where(User.tg_id == tg_id)) # Поиск пользователя по Telegram ID
        if not user: # Проверка, существует ли пользователь
            session.add(User(tg_id=tg_id)) # Добавление нового пользователя
            await session.commit() # Фиксация создания пользователя
            user = await session.scalar(select(User).where(User.tg_id == tg_id)) # Повторный поиск пользователя
            if not user: # Проверка, создан ли пользователь
                raise Exception("Failed to create user") # Выброс исключения при неудачном создании пользователя
        new_task = Task(task=task, user=user.id) # Создание новой задачи с текстом и ID пользователя
        session.add(new_task) # Добавление задачи в сессию
        await session.commit() # Фиксация изменений
        await session.refresh(new_task) # Обновление данных задачи из базы
        return new_task.id # Возврат ID новой задачи

async def del_task(task_id):
    async with async_session() as session: # Создание асинхронной сессии
        task = await session.get(Task, task_id) # Получение задачи по её ID
        if task: # Проверка, существует ли задача
            await session.delete(task) # Удаление задачи из базы данных
            await session.commit() # Фиксация изменений
            return True # Возврат True при успешном удалении
        return False # Возврат False, если задача не найдена

async def update_task(task_id, new_text):
    async with async_session() as session: # Создание асинхронной сессии
        task = await session.get(Task, task_id) # Получение задачи по её ID
        if task: # Проверка, существует ли задача
            task.task = new_text # Обновление текста задачи
            await session.commit() # Фиксация изменений
            await session.refresh(task) # Обновление данных задачи из базы
            return True # Возврат True при успешном обновлении
        return False # Возврат False, если задача не найдена

async def set_reminder(task_id, remind_time):
    async with async_session() as session: # Создание асинхронной сессии
        session.add(Reminder(task_id=task_id, remind_time=remind_time)) # Добавление нового напоминания с указанным временем
        await session.commit() # Фиксация изменений

async def get_user_by_task_id(task_id):
    async with async_session() as session: # Создание асинхронной сессии
        task = await session.get(Task, task_id) # Получение задачи по её ID
        if not task: # Проверка, существует ли задача
            return None # Возврат None, если задача не найдена
        user = await session.get(User, task.user) # Получение пользователя по ID, связанному с задачей
        return user.tg_id if user else None # Возврат Telegram ID пользователя или None, если пользователь не найден

async def get_active_reminders():
    async with async_session() as session: # Создание асинхронной сессии
        reminders = await session.scalars(
            select(Reminder).where(Reminder.is_active == True)) # Выполнение запроса на выборку активных напоминаний
        return reminders.all() # Возврат списка всех активных напоминаний

async def deactivate_reminder(reminder_id):
    async with async_session() as session: # Создание асинхронной сессии
        reminder = await session.get(Reminder, reminder_id) # Получение напоминания по его ID
        if reminder: # Проверка, существует ли напоминание
            reminder.is_active = False # Деактивация напоминания
            await session.commit() # Фиксация изменений
            return True # Возврат True при успешной деактивации
        return False # Возврат False, если напоминание не найдено

async def get_task_by_id(task_id):
    async with async_session() as session: # Создание асинхронной сессии
        task = await session.scalar(
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.reminders))) # Выполнение запроса на выборку задачи с подгрузкой связанных напоминаний
        return task # Возврат найденной задачи или None

async def delete_user_data(tg_id):
    async with async_session() as session: # Создание асинхронной сессии
        user = await session.scalar(select(User).where(User.tg_id == tg_id)) # Поиск пользователя по Telegram ID
        if not user: # Проверка, существует ли пользователь
            return False # Возврат False, если пользователь не найден
        tasks = await session.scalars(
            select(Task).where(Task.user == user.id)) # Получение всех задач пользователя
        for task in tasks: # Перебор всех задач
            await session.delete(task) # Удаление каждой задачи
        await session.commit() # Фиксация изменений
        return True # Возврат True при успешном удалении

async def deactivate_reminder_by_task(task_id):
    async with async_session() as session: # Создание асинхронной сессии
        reminders = await session.scalars(
            select(Reminder)
            .where(Reminder.task_id == task_id, Reminder.is_active == True)) # Получение всех активных напоминаний для задачи
        for reminder in reminders: # Перебор каждого напоминания
            reminder.is_active = False # Деактивация напоминания
        await session.commit() # Фиксация изменений
        return bool(reminders.all()) # Возврат True, если были найдены напоминания

async def update_reminder_time(reminder_id, new_time):
    async with async_session() as session: # Создание асинхронной сессии
        reminder = await session.get(Reminder, reminder_id) # Получение напоминания по его ID
        if reminder: # Проверка, существует ли напоминание
            reminder.remind_time = new_time # Обновление времени напоминания
            await session.commit() # Фиксация изменений
            return True # Возврат True при успешном обновлении
        return False # Возврат False, если напоминание не найдено