from datetime import datetime

from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import MSK
from db.models import Users
from filters.is_private import PrivateChatFilter
from handlers.user.tariff import tariff_manager

router = Router()


@router.message(PrivateChatFilter(), Command('info'))  # Информация о подписке
async def info_sub(message: Message, session: AsyncSession):
    user = (await session.execute(select(Users).where(Users.user_id == message.from_user.id))).scalar_one_or_none()
    if not user:
        return

    if not user.tariff:
        return await message.reply('⭐ <b>У вас ещё нет активной подписки. Может, самое время приобрести?</b>',
                                   parse_mode=ParseMode.HTML)

    tariff = tariff_manager.tariffs.get(user.tariff)
    if not tariff:
        return

    now = datetime.now(MSK)
    time_left = user.time_sub - now

    days = time_left.days
    hours = time_left.seconds // 3600

    await message.answer(f"<b>💎 Информация о подписке:</b>\n\n"
                         f"<blockquote>🔋 <b>Текущий тариф:</b> <code>{tariff.name}</code></blockquote>\n"
                         f"<blockquote>⏳ <b>Время до окончания тарифа:</b> <code>{days}д. {hours}ч.</code></blockquote>",
                         parse_mode=ParseMode.HTML)
