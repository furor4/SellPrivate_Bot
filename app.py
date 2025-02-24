import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import bot, dp
from db.models import create_tables, DatabaseMiddleware
from handlers.admin import without_adding, stats
from handlers.user import start, tariff, purchased, sub_info, expiration_check
from handlers.user.expiration_check import check_subscriptions, check_expired_subscriptions

logging.getLogger('aiogram').setLevel(logging.INFO)

scheduler = AsyncIOScheduler(timezone='Europe/Moscow')  # Часовой пояс - МСК


async def main():
    await create_tables()
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    dp.include_routers(start.router, without_adding.router, tariff.router, stats.router, purchased.router,
                       sub_info.router, expiration_check.router)
    try:
        scheduler.add_job(check_subscriptions, 'cron', hour=10, minute=00)  # Проверка на то, остался ли день до окончания подписки. Ежедневно в 10:00
        scheduler.add_job(check_expired_subscriptions, 'interval', minutes=15)  # Проверка на уже истечённую подписку каждые 15 минут
        scheduler.start()
        await bot.delete_webhook(drop_pending_updates=True)
        print(f'Запущено.')
        await dp.start_polling(bot)

    except Exception as e:
        logging.exception(f"Ошибка при запуске бота: {e}")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, RuntimeError) as main_error:
        print('Бот выключен.')
