import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramRetryAfter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import MSK, CHANNEL_ID, CHAT_ID, bot
from db.models import Users, async_session
from filters.is_private import PrivateChatFilter
from handlers.user.tariff import tariff_manager

router = Router()


# Проверка на день до конца срока подписки
async def check_subscriptions():
    now = datetime.now(MSK)

    expiration_threshold = now + timedelta(days=1)

    async with async_session() as session:
        users_to_notify = (await session.execute(
            select(Users).where(Users.time_sub > now, Users.time_sub <= expiration_threshold)
        )).scalars().all()

        for user in users_to_notify:
            await send_subscription_expiration_notification(user)


# Отправление напоминания о дне до конца срока подписки
async def send_subscription_expiration_notification(user: Users):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛔ Отменить подписку", callback_data="cancel_subscription_confirm"),
         InlineKeyboardButton(text="❤️ Продлить", callback_data="extend_subscription")]
    ])

    try:
        await bot.send_message(
            chat_id=user.user_id,
            text="👋 <b>Снова приветствую! Завтра истекает срок вашей подписки.</b>"
                 "\n\n<blockquote>🔓 <b>Чтобы и дальше получать доступ к эксклюзивным материалам, <u>пожалуйста, "
                 "продлите подписку.</u></b></blockquote>",
            parse_mode=ParseMode.HTML,
            reply_markup=kb
        )
    except Exception as e:
        print(f"Не удалось отправить уведомление пользователю {user.user_id}: {e}")


@router.callback_query(PrivateChatFilter(), F.data == "cancel_subscription_confirm")  # Подтверждение отмены подписки
async def cancel_subscription_confirm(cq: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Не отменять", callback_data="cancel_subscription_deny"),
         InlineKeyboardButton(text="✅ Да, уверен(-а)", callback_data="cancel_subscription")]
    ])

    await cq.message.edit_text("❓ <b>Вы уверены, что хотите отменить подписку на NSFW?</b>", reply_markup=kb,
                               parse_mode=ParseMode.HTML)


@router.callback_query(PrivateChatFilter(), F.data == "cancel_subscription_deny")  # Человек не отменил подписку
async def cancel_subscription_deny(cq: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛔ Отменить подписку", callback_data="cancel_subscription_confirm"),
         InlineKeyboardButton(text="❤️ Продлить", callback_data="extend_subscription")]
    ])

    await cq.message.edit_text("✨ <b>Спасибо, что остаётесь с нами.</b>", reply_markup=kb,
                               parse_mode=ParseMode.HTML)


@router.callback_query(PrivateChatFilter(), F.data == "extend_subscription")  # Человек продлевает подписку
async def extend_subscription(cq: CallbackQuery):
    await tariff_manager.send_tariff_selection_message(cq)


# Функция бана человека по истечению срока подписки
async def ban_user(user_id: int, chat_id: int):
    try:
        await bot.ban_chat_member(
            chat_id=chat_id,
            user_id=user_id,
            until_date=0
        )
        await bot.unban_chat_member(
            chat_id=chat_id,
            user_id=user_id
        )
    except Exception as e:
        print(f"Не удалось кикнуть пользователя {user_id} из ресурса {chat_id}: {e}")


@router.callback_query(PrivateChatFilter(), F.data == "cancel_subscription")  # Отмена подписки
async def cancel_subscription(cq: CallbackQuery, session: AsyncSession):
    user_id = cq.from_user.id

    user = (await session.execute(select(Users).where(Users.user_id == user_id))).scalar_one_or_none()
    if not user:
        return

    await ban_user(user_id, CHANNEL_ID)  # Бан в канале
    await ban_user(user_id, CHAT_ID)  # Бан в чате (если существует)
    await bot.revoke_chat_invite_link(chat_id=CHANNEL_ID, invite_link=user.link)  # Сброс ссылки

    user.tariff = None
    user.time_sub = None
    user.link = None
    await session.commit()

    await cq.message.edit_text("🚩 <b>Подписка была успешно отменена. С нетерпением жду вашей следующей покупки!</b>",
                               reply_markup=None, parse_mode=ParseMode.HTML)


# Функция проверки на истечение срока подписки
async def check_expired_subscriptions():
    now = datetime.now(MSK)

    async with async_session() as session:
        expired_users = (await session.execute(select(Users).where(Users.time_sub <= now,
                                                                   Users.tariff != None))).scalars().all()
        for user in expired_users:
            try:
                await ban_user(user.user_id, CHANNEL_ID)
                await ban_user(user.user_id, CHAT_ID)

                if user.link:
                    try:
                        await bot.revoke_chat_invite_link(chat_id=CHANNEL_ID, invite_link=user.link)
                    except TelegramBadRequest:
                        pass

                user.tariff = None
                user.time_sub = None
                user.link = None
                await session.commit()

                try:
                    await bot.send_message(
                        chat_id=user.user_id,
                        text="<b>😔 Упс! Кажется, ваша подписка истекла!</b>"
                             "\n\n<blockquote><b><u>💙 Но не переживай!</u> Ты всегда можешь вернуть себе доступ к "
                             "эксклюзивному контенту, прописав команду</b> /start.</blockquote>",
                        parse_mode=ParseMode.HTML
                    )
                except TelegramForbiddenError:
                    logging.info(f"Пользователь {user.user_id} заблокировал бота. Уведомление не отправлено.")
                except TelegramRetryAfter as e:
                    await asyncio.sleep(e.retry_after)
                except TelegramBadRequest as e:
                    logging.error(f"Ошибка при отправке {user.user_id}: {e}")

            except Exception as e:
                logging.exception(f"Ошибка при обработке юзера {user.user_id}: {e}")
                await session.rollback()
