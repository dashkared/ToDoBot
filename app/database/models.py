from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey, String
from datetime import datetime
from sqlalchemy import DateTime

engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3') # Создание асинхронного движка для подключения к SQLite базе данных

async_session = async_sessionmaker(engine) # Создание фабрики асинхронных сессий для работы с базой данных


class Base(AsyncAttrs, DeclarativeBase):
    pass # Определение базового класса для моделей SQLAlchemy с поддержкой асинхронных операций


class User(Base):
    __tablename__ = 'users' # Указание имени таблицы в базе данных
    id: Mapped[int] = mapped_column(primary_key=True) # Определение столбца ID как первичного ключа
    tg_id = mapped_column(BigInteger) # Определение столбца для Telegram ID пользователя


from sqlalchemy.orm import relationship, Mapped, mapped_column

class Task(Base):
    __tablename__ = 'tasks' # Указание имени таблицы в базе данных

    id: Mapped[int] = mapped_column(primary_key=True) # Определение столбца ID как первичного ключа
    task: Mapped[str] = mapped_column(String(100)) # Определение столбца для текста задачи с максимальной длиной 100 символов
    user: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE')) # Определение внешнего ключа, связывающего задачу с пользователем, с каскадным удалением
    reminders = relationship("Reminder", back_populates="task", cascade="all, delete-orphan") # Определение связи с таблицей напоминаний с каскадным удалением

class Reminder(Base):
    __tablename__ = 'reminders' # Указание имени таблицы в базе данных

    id: Mapped[int] = mapped_column(primary_key=True) # Определение столбца ID как первичного ключа
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id', ondelete='CASCADE')) # Определение внешнего ключа, связывающего напоминание с задачей, с каскадным удалением
    remind_time: Mapped[datetime] = mapped_column(DateTime) # Определение столбца для времени напоминания
    is_active: Mapped[bool] = mapped_column(default=True) # Определение столбца для статуса активности напоминания
    task = relationship("Task", back_populates="reminders") # Определение обратной связи с таблицей задач


async def async_main():
    async with engine.begin() as conn: # Создание асинхронного соединения с базой данных
        await conn.run_sync(Base.metadata.create_all) # Создание всех таблиц, определённых в моделях