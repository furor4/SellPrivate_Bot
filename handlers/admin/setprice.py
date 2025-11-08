from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from filters.is_owner import IsOwner
from filters.is_private import PrivateChatFilter
from handlers.user.tariff import tariff_manager

router = Router()

@router.message(PrivateChatFilter(), IsOwner(), Command("setprice"))
async def set_tariff_price(message: Message):
    try:
        args = message.text.split()
        if len(args) != 3:
            raise ValueError

        tariff_name = args[1]
        new_price = int(args[2])

        success = tariff_manager.update_tariff_price(tariff_name, new_price)
        if success:
            await message.answer(f"✅ Цена тарифа {tariff_name} успешно изменена на {new_price}₽")
        else:
            await message.answer("❌ Тариф с таким названием не найден. Доступные тарифы: month, sixmonth, year")

    except ValueError:
        await message.answer(
            "❌ Неправильный формат команды. Используйте: /setprice <тариф> <цена>\nПример: /setprice month 250")