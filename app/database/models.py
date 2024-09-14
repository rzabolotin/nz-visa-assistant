from datetime import datetime

from config import DATABASE_URL
from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Dialog(Base):
    __tablename__ = "dialogs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    query = Column(Text)
    answer = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)


engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_dialog(user_id: int, query: str, answer: str):
    async with AsyncSessionLocal() as session:
        dialog = Dialog(user_id=user_id, query=query, answer=answer)
        session.add(dialog)
        await session.commit()
