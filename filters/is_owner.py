from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

from config import OWNER_ID


class IsOwner(BaseFilter):  # Фильтр проверки на владельца
    async def __call__(self, obj: Message | CallbackQuery) -> bool:
        if isinstance(obj, Message):
            return obj.from_user.id == OWNER_ID
        elif isinstance(obj, CallbackQuery):
            return obj.from_user.id == OWNER_ID
        return False
