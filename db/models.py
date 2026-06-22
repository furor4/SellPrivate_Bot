from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy import Column, Integer, BigInteger, String, DateTime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)

Base = declarative_base()
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class DatabaseMiddleware(BaseMiddleware):  # Мидлварь для внедрения сессии базы данных в обработчики
    async def __call__(self, handler, event: TelegramObject, data: dict):
        async with async_session() as session:
            data["session"] = session
            return await handler(event, data)


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    fullname = Column(String, nullable=False)
    tariff = Column(String)  # Купленный тариф
    time_sub = Column(DateTime(timezone=True))  # Время до окончания подписки
    link = Column(String)  # Выданная пользователю ссылка


class PriceData(Base):
    __tablename__ = "price_data"
    id = Column(Integer, primary_key=True, autoincrement=True)
    month = Column(Integer, default=100)
    sixmonth = Column(Integer, default=500)
    year = Column(Integer, default=1000)


class Stats(Base):
    __tablename__ = "stats"
    id = Column(Integer, primary_key=True)
    total_money = Column(BigInteger, default=0)  # Общая сумма полученных денег
    monthly_subs = Column(BigInteger, default=0)  # Кол-во купивших за месяц
    sixmonthly_subs = Column(BigInteger, default=0)
    yearly_subs = Column(BigInteger, default=0)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
