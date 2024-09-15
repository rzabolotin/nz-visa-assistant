from datetime import datetime

from config import DATABASE_URL
from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Dialog(Base):
    __tablename__ = "dialogs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    query = Column(Text)
    answer = Column(Text)
    input_tokens_count = Column(BigInteger)
    output_tokens_count = Column(BigInteger)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    dialog_id = Column(Integer, index=True)
    is_positive = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.utcnow)


engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_dialog(
    user_id: int, query: str, answer: str, input_tokens: int, output_tokens: int
):
    async with AsyncSessionLocal() as session:
        try:
            dialog = Dialog(
                user_id=user_id,
                query=query,
                answer=answer,
                input_tokens_count=input_tokens,
                output_tokens_count=output_tokens,
            )
            session.add(dialog)
            await session.commit()
            return dialog.id
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to save dialog: {str(e)}")


async def save_feedback(dialog_id: int, is_positive: bool):
    async with AsyncSessionLocal() as session:
        try:
            feedback = Feedback(
                dialog_id=dialog_id,
                is_positive=is_positive,
            )
            session.add(feedback)
            await session.commit()
            return feedback.id
        except Exception as e:
            await session.rollback()
            raise Exception(f"Failed to save feedback: {str(e)}")
