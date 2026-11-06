import os
import sys
import asyncio
import logging

# Loyiha ildiz katalogini Python path ga qo'shish
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from aiogram import Bot, Dispatcher
from app import create_app
from app.config import Config
from app.models.setting import Setting
from bot.handlers.common import common_router
from bot.handlers.subscription import sub_router
from bot.handlers.freeze import freeze_router
from bot.handlers.qr_code import qr_router
from bot.handlers.history import history_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
logger = logging.getLogger("IronFitnessBot")

async def main():
    flask_app = create_app()

    with flask_app.app_context():
        token = Config.TELEGRAM_BOT_TOKEN or Setting.get_value('telegram_bot_token', '')

    if not token or token.startswith('7891234567'):
        logger.warning(
            "==========================================================\n"
            "OGOHLANTIRISH: TELEGRAM_BOT_TOKEN kiritilmagan yoki test qiymatida!\n"
            "Botni ishga tushirish uchun .env faylida TELEGRAM_BOT_TOKEN ni sozlang.\n"
            "=========================================================="
        )
        print("Bot tokeni topilmadi. .env fayliga haqiqiy token kiriting.")
        return

    bot = Bot(token=token)
    dp = Dispatcher()

    # Flask ilova kontekstini routerlarga uzatish (Dependency injection)
    dp['flask_app'] = flask_app

    # Routerlarni ulash
    dp.include_router(common_router)
    dp.include_router(sub_router)
    dp.include_router(freeze_router)
    dp.include_router(qr_router)
    dp.include_router(history_router)

    logger.info("IRON FITNESS CLUB Telegram boti ishga tushdi...")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
