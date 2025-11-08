from datetime import datetime

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import bot, OWNER_ID, CHANNEL_ID, MSK
from db.models import Users, Stats
from filters.is_owner import IsOwner
from filters.is_private import PrivateChatFilter
from handlers.user.tariff import tariff_manager, Tariff

router = Router()


@router.callback_query(PrivateChatFilter(), F.data.startswith('buy_confirm_'))  # Кнопка подтверждения оплаты
async def confirm_payment(cq: CallbackQuery, session: AsyncSession):
    tariff_type = cq.data.split('_')[2]
    user_id = cq.from_user.id

    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()

    if not user:
        return

    await bot.send_message(chat_id=cq.message.chat.id, text='🕒 <i>Ожидайте, проверяем платёж...</i>',
                           parse_mode=ParseMode.HTML)  # Заказчику отправляется сообщение о проверке платежа
    await bot.delete_message(chat_id=cq.message.chat.id, message_id=cq.message.message_id)

    msk = datetime.now(MSK).strftime("%Y-%m-%d %H:%M:%S")
    tariff_obj = tariff_manager.get_tariff(tariff_type)
    tariff_text = tariff_obj.name
    tariff_price = tariff_obj.price

    admin_message = (f"💸 <b>У вас покупка!</b> <u>Пожалуйста, подтвердите поступление средств.</u>"
                     f"\n\n<blockquote><b>👤 Покупатель:</b> <a href='tg://user?id={user.user_id}'>{user.fullname}"
                     f"</a></blockquote>"
                     f"\n<blockquote><b>🔋 Тариф:</b> {tariff_text} ({tariff_price}₽)</blockquote>"
                     f"\n<blockquote>🕰️ Время покупки: {msk} (МСК)</blockquote>")

    admin_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтверждаю", callback_data=f"admin_confirm_payment_{user_id}_{tariff_type}")],
        [InlineKeyboardButton(text="❌ Отклоняю", callback_data=f"admin_cancel_payment_{user_id}_{tariff_type}")]
    ])

    await bot.send_message(chat_id=OWNER_ID, text=admin_message, parse_mode=ParseMode.HTML,
                           reply_markup=admin_kb, disable_web_page_preview=True)  # Владельцу отправляется сообщение о покупке


@router.callback_query(PrivateChatFilter(), IsOwner(), F.data.startswith('admin_confirm_payment_'))  # Владелец подтвердил платёж
async def admin_confirm_payment(cq: CallbackQuery, session: AsyncSession, tariff: Tariff):
    user_id, tariff_type = cq.data.split('_')[3:5]
    user_id = int(user_id)

    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    if not user:
        return

    invite_link_obj = await bot.create_chat_invite_link(
        chat_id=CHANNEL_ID,
        member_limit=1
    )
    invite_link = invite_link_obj.invite_link  # Сгенерирована одноразовая ссылка в канал

    expiration_date = tariff.get_expiration_date(datetime.now(MSK))

    user.time_sub = expiration_date  # Установка даты окончания срока подписки
    user.tariff = tariff_type  # Установка за пользователем купленного тарифа в БД
    tariff = tariff_manager.get_tariff(tariff_type)

    stats = (await session.execute(select(Stats).where(Stats.id == 1))).scalar_one_or_none()
    if not stats:
        stats = Stats()
        session.add(stats)
        await session.commit()

    stats.total_money += tariff.price
    if tariff_type == 'month':
        stats.monthly_subs += 1
    elif tariff_type == 'sixmonth':
        stats.sixmonthly_subs += 1
    else:
        stats.yearly_subs += 1

    await session.commit()

    if user.link:  # Если у человека уже была ссылка, то он продлевает платёж
        await cq.message.edit_text(f"✅ <b>Платёж подтверждён! Подписка пользователя продлена!</b>"
                                   f"\n\n<blockquote><b>👤 Покупатель: <a href='tg://user?id={user.user_id}'>"
                                   f"{user.fullname}</a></b></blockquote>"
                                   f"\n<blockquote><b>🔗 Ссылка:</b> {user.link}</blockquote>",
                                   parse_mode=ParseMode.HTML, reply_markup=None)
        await bot.send_message(chat_id=user_id, text=f"🚀 <b>Поздравляю с продлением подписки на ещё {tariff.duration}!"
                                                     f" Будем радовать вас и впредь.</b>", parse_mode=ParseMode.HTML)
        await session.commit()
        return

    user.link = invite_link
    await session.commit()

    # Если ссылки не было, человек покупает в первый раз.
    await cq.message.edit_text(f"✅ <b>Платёж подтверждён!</b>"
                               f"\n\n<blockquote><b>👤 Покупатель: <a href='tg://user?id={user.user_id}'>"
                               f"{user.fullname}</a></b></blockquote>"
                               f"\n<blockquote><b>🔗 Выдана ссылка:</b> {user.link}</blockquote>",
                               parse_mode=ParseMode.HTML, reply_markup=None)

    await bot.send_message(chat_id=user_id,
                           text=f"🚀 <b>Поздравляю с приобретением подписки на {tariff.duration}!</b>"
                                f"\n\n<blockquote><i>🔗 Ваша личная ссылка:</i> {invite_link}</blockquote>",
                           parse_mode=ParseMode.HTML)


@router.callback_query(PrivateChatFilter(), IsOwner(), F.data.startswith('admin_cancel_payment_'))  # Владелец отклонил платёж
async def admin_cancel_payment(cq: CallbackQuery):
    user_id, tariff_type = cq.data.split('_')[3:5]
    user_id = int(user_id)

    await cq.message.edit_text('❌ Операция отклонена.', reply_markup=None)

    await bot.send_message(chat_id=user_id, text='❌ <b>Ваша операция была отклонена.</b>', parse_mode=ParseMode.HTML)
