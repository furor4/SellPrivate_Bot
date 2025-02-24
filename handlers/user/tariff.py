from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, CallbackQuery, InlineKeyboardButton

from filters.is_private import PrivateChatFilter

router = Router()


# Класс тарифа
class Tariff:
    def __init__(self, name: str, price: str, duration: str, callback_data):
        self.name = name
        self.price = price
        self.duration = duration
        self.callback_data = callback_data

    def get_payment_message(self):
        return (f'<blockquote><b>💰 Цена доступа:</b> <code>{self.price}</code></blockquote>'
                f'\n<blockquote><b>🔋 Тариф:</b> <code>{self.duration}</code></blockquote>'
                f'\n————————————————————————'
                f'\n<blockquote><b>‼️ Пожалуйста, переведите указанную выше сумму на данные'
                f' реквизиты:</b></blockquote>'
                f'\n<blockquote>┖ УКАЖИТЕ СВОИ РЕКВИЗИТЫ</blockquote>'
                f'\n<blockquote><i>🔻 После оплаты нажмите на кнопку снизу</i></blockquote>')


# Управление тарифами (с возможностью добавить новые)
class TariffManager:
    def __init__(self):
        self.tariffs = {
            'month': Tariff(
                name='🌙 Месяц',
                price='200₽',
                duration='1 месяц',
                callback_data='buy_confirm_month'
            ),
            'sixmonth': Tariff(
                name='🌕 6 месяцев',
                price='900₽',
                duration='6 месяцев',
                callback_data='buy_confirm_sixmonth'
            ),
            'year': Tariff(
                name='🌚 1 год',
                price='1200₽',
                duration='1 год',
                callback_data='buy_confirm_year'
            )
        }

    def get_tariff(self, tariff_name: str) -> Tariff:  # Возвращает объект тарифа по его имени
        return self.tariffs.get(tariff_name)

    def get_tariff_selection_keyboard(self) -> InlineKeyboardMarkup:  # Формирует клавиатуру с кнопками для выбора тарифа
        inline_keyboard = []
        row = []
        for tariff_name, tariff in self.tariffs.items():
            button = InlineKeyboardButton(text=f'{tariff.name}', callback_data=f'buy_access_{tariff_name}')
            row.append(button)
            if len(row) == 2:  # ДЛИНА КЛАВИАТУРЫ ТАРИФОВ
                inline_keyboard.append(row)
                row = []

        if row:
            inline_keyboard.append(row)

        kb = InlineKeyboardMarkup(inline_keyboard=inline_keyboard)
        return kb

    async def send_tariff_selection_message(self, cq: CallbackQuery):  # Отправляет сообщение с предложением выбрать тариф
        text = '<b>💡 Прошу, выберите интересующий вас тариф ниже:</b>'

        keyboard = self.get_tariff_selection_keyboard()

        await cq.message.edit_text(text=text, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    @staticmethod
    async def send_payment_message(cq: CallbackQuery, tariff: Tariff):  # Отправляет сообщение с информацией об оплате выбранного тарифа
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='✅ Оплатил(-а)', callback_data=tariff.callback_data)],
            [InlineKeyboardButton(text='🔙 К выбору тарифа', callback_data='back_to_tariff')]
        ]
        )

        text = tariff.get_payment_message()

        await cq.message.edit_text(text=text, reply_markup=kb, parse_mode=ParseMode.HTML)


tariff_manager = TariffManager()


@router.callback_query(PrivateChatFilter(), F.data == 'choosing_tariff')
async def choosing_tariff_cq(cq: CallbackQuery):
    await tariff_manager.send_tariff_selection_message(cq)


@router.callback_query(PrivateChatFilter(), F.data == 'back_to_tariff')
async def back_to_tariff_cq(cq: CallbackQuery):
    await tariff_manager.send_tariff_selection_message(cq)


@router.callback_query(PrivateChatFilter(), F.data.startswith('buy_access_'))
async def buy_access_cq(cq: CallbackQuery):
    tariff_name = cq.data.split('_')[2]
    tariff = tariff_manager.get_tariff(tariff_name)

    await tariff_manager.send_payment_message(cq, tariff)
