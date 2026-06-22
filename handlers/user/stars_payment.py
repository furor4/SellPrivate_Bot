from datetime import datetime

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.types import Message, PreCheckoutQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import bot, CHANNEL_ID, MSK
from db.models import Users, Stats
from handlers.user.tariff import tariff_manager

router = Router()

@router.pre_checkout_query()
async def pre_checkout(pcq: PreCheckoutQuery):
    await pcq.answer(ok=True)

@router.message(F.successful_payment)
async def successful_payment(message: Message, session: AsyncSession):
    payload = message.successful_payment.invoice_payload
    _, user_id_str, tariff_type = payload.split('_')
    user_id = int(user_id_str)

    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    if not user:
        return

    invite_link_obj = await bot.create_chat_invite_link(chat_id=CHANNEL_ID, member_limit=1)
    invite_link = invite_link_obj.invite_link

    tariff = tariff_manager.get_tariff(tariff_type)
    expiration_date = tariff.get_expiration_date(datetime.now(MSK))

    user.time_sub = expiration_date
    user.tariff = tariff_type

    stats = (await session.execute(select(Stats).where(Stats.id == 1))).scalar_one_or_none()
    if not stats:
        stats = Stats()
        session.add(stats)

    stats.total_money += tariff.price
    if tariff_type == 'month':
        stats.monthly_subs += 1
    elif tariff_type == 'sixmonth':
        stats.sixmonthly_subs += 1
    else:
        stats.yearly_subs += 1

    if user.link:
        await message.answer("✅ <b>Платёж подтверждён!</b>\n"
                             f"Ваша подписка успешно продлена до {expiration_date.strftime('%d.%m.%Y %H:%M')}.\n\n"
                             f"Ваша ссылка для входа: {user.link}", parse_mode=ParseMode.HTML)
    else:
        user.link = invite_link
        await message.answer(f"🚀 <b>Поздравляю с приобретением подписки на {tariff.duration}</b>.\n\n"
                             f"Ваша ссылка для входа: {user.link}")

    await session.commit()