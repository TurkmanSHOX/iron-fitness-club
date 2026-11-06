import os
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from app.models.client import TelegramUser
from app.config import Config
from app.services.pdf_service import generate_qr_code_image

qr_router = Router()

@qr_router.message(F.text == "📱 Mening QR-kodim")
async def send_my_qr_code(message: Message, flask_app):
    """Mijozga uning shaxsiy kirish QR-kod rasmini yuborish"""
    with flask_app.app_context():
        tg_user = TelegramUser.query.filter_by(telegram_id=message.from_user.id).first()
        if not tg_user or not tg_user.client_id:
            await message.answer("Iltimos, avval telefon raqamingizni yuborib ro'yxatdan o'ting.")
            return

        client = tg_user.client
        qr_token = client.qr_code

        qr_img_name = f"qr_{client.id}_{qr_token}.png"
        qr_img_path = os.path.join(Config.QRCODES_FOLDER, qr_img_name)

        if not os.path.exists(qr_img_path):
            generate_qr_code_image(qr_token, qr_img_path)

        photo = FSInputFile(qr_img_path)
        caption = (
            f"📱 <b>Sizning Shaxsiy QR-kodingiz:</b>\n\n"
            f"F.I.Sh.: <b>{client.full_name}</b>\n"
            f"Kod: <code>{qr_token}</code>\n\n"
            f"💡 <i>Zalga kirishda ushbu QR-kodni receptiondagi 2D skanerga ko'rsating.</i>"
        )

        await message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML"
        )
