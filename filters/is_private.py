from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class PrivateChatFilter(BaseFilter):  # Фильтр проверки на ЛС
    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        if isinstance(obj, Message):
            return obj.chat.type == "private"
        elif isinstance(obj, CallbackQuery):
            return obj.message.chat.type == "private"
        return False
