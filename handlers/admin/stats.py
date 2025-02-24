from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Stats
from filters.is_owner import IsOwner
from filters.is_private import PrivateChatFilter

router = Router()


@router.message(PrivateChatFilter(), IsOwner(), F.text.strip().lower().in_(['стата', 'стат', 'статистика']))  # Статистика покупок для владельца
@router.message(PrivateChatFilter(), IsOwner(), Command('stats'))
async def statistics(message: Message, session: AsyncSession):
    stats = await session.scalar(select(Stats).where(Stats.id == 1))
    if not stats:
        return

    text = (
        "📊 <b>Статистика продаж:</b>\n\n"
        f"<blockquote><b>💵 Всего денег получено:</b> <code>{stats.total_money}₽</code></blockquote>\n"
        f"<blockquote><b>🌙 Куплено месячных подписок:</b> <code>{stats.monthly_subs}</code></blockquote>\n"
        f"<blockquote><b>🌕 Куплено шестимесячных подписок:</b> <code>{stats.sixmonthly_subs}</code></blockquote>\n"
        f"<blockquote><b>🌚 Куплено годовых подписок:</b> <code>{stats.yearly_subs}</code></blockquote>")

    await message.reply(text, parse_mode=ParseMode.HTML)
