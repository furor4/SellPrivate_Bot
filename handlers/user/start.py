from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Users, Stats
from filters.is_private import PrivateChatFilter

router = Router()


@router.message(PrivateChatFilter(), CommandStart())
async def start(message: Message, session: AsyncSession):
    user_id = message.from_user.id
    fullname = message.from_user.full_name

    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    if not user:
        user = Users(user_id=user_id, fullname=fullname)
        session.add(user)
        await session.commit()

    stats = (await session.execute(select(Stats).where(Stats.id == 1))).scalar_one_or_none()
    if not stats:
        stats = Stats()
        session.add(stats)
        await session.commit()

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🔓 Получить доступ', callback_data='choosing_tariff')]
        ]
    )

    text = '...'  # Сюда введите свой текст, который бот отправляет при старте

    await message.reply(text, reply_markup=kb, parse_mode=ParseMode.HTML)
