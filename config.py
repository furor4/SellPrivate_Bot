import pytz
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from environs import Env

env = Env()
env.read_env('.env')

TOKEN = env.str('TOKEN')
OWNER_ID = env.int('ADMIN')
CHANNEL_ID = env.int('PRIVATE_CHANNEL_ID')
CHAT_ID = env.int('PRIVATE_CHAT_ID')

DB_USER = env.str('DB_USER')
DB_PASSWORD = env.str('DB_PASSWORD')
DB_NAME = env.str('DB_NAME')

DATABASE_URL = env.str(f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@postgres_db:5432/{DB_NAME}')

MSK = pytz.timezone('Europe/Moscow')  # Время по МСК
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
