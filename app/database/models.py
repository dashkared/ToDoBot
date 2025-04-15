from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy import BigInteger
from sqlalchemy import ForeignKey, String
engine = create_async_engine(url ='sqlite+aiosqlite:///db.sqlite3')

async_session = async_sessionmaker(engine)


class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    
class Task(Base):
    __tablename__ = 'tasks'
    
    id : Mapped[int] = mapped_column(primary_key=True)
    task: Mapped[str] = mapped_column(String(100))
    user: Mapped[int] = mapped_column(ForeignKey('users.id'))
    


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
