import pytz
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from environs import Env

env = Env()
env.read_env('.env')

TOKEN = env.str('TOKEN')
OWNER_ID = env.int('ADMIN')  # Владелец приватки
CHANNEL_ID = env.int('PRIVATE_CHANNEL_ID')  # Айди канала приватки
CHAT_ID = env.int('PRIVATE_CHAT_ID')  # Айди чата приватки (если существует)
MSK = pytz.timezone('Europe/Moscow')  # Время по МСК
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
