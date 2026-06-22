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
DATABASE_URL = env.str('DATABASE_URL')

MSK = pytz.timezone('Europe/Moscow')  # Время по МСК
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
