from aiogram import Router
from aiogram.enums import ParseMode
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION
from aiogram.types import ChatMemberUpdated

from config import bot, CHANNEL_ID, CHAT_ID

router = Router()


@router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION))
async def bot_added_to_group(event: ChatMemberUpdated):
    chat_id = event.chat.id

    if chat_id in [CHANNEL_ID, CHAT_ID]:
        return

    await bot.send_message(chat_id=chat_id, text="💬 <b>Я предназначен для использования в личных сообщениях.</b>"
                                                 "\n\n<blockquote><i>Если вам требуются мои услуги, пожалуйста, "
                                                 "напишите мне в ЛС.</i></blockquote>", parse_mode=ParseMode.HTML)
    await bot.leave_chat(chat_id=chat_id)
