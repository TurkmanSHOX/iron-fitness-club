import os
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from bot.keyboards.default import get_contact_keyboard, get_main_menu
from app.extensions import db
from app.models.client import Client, TelegramUser, ClientQRCode
from app.models.setting import Setting
from app.services.pdf_service import generate_qr_code_image
from app.config import Config

common_router = Router()

@common_router.message(CommandStart())
async def cmd_start(message: Message, flask_app):
    """Foydalanuvchi /start yuborganda ro'yxatdan o'tganligini tekshirish"""
    with flask_app.app_context():
        tg_user = TelegramUser.query.filter_by(telegram_id=message.from_user.id).first()
        club_name = Setting.get_value('club_name', 'IRON FITNESS CLUB')

        if tg_user and tg_user.client_id:
            client = tg_user.client
            await message.answer(
                f"Assalomu alaykum, <b>{client.full_name}</b>!\n\n"
                f"<b>{club_name}</b> rasmiy botiga xush kelibsiz! Quyidagi menyu orqali xizmatlardan foydalanishingiz mumkin:",
                reply_markup=get_main_menu(),
                parse_mode="HTML"
            )
        else:
            await message.answer(
                f"Assalomu alaykum! <b>{club_name}</b> sport zali rasmiy botiga xush kelibsiz!\n\n"
                f"Tizimdan to'liq foydalanish, abonement xarid qilish va shaxsiy QR-kodingizni olish uchun "
                f"iltimos, pastdagi tugma orqali telefon raqamingizni tasdiqlang:",
                reply_markup=get_contact_keyboard(),
                parse_mode="HTML"
            )


@common_router.message(F.contact)
async def handle_contact(message: Message, flask_app):
    """Mijoz telefon raqamini yuborganda profili bilan bog'lash yoki yangi profil yaratish"""
    contact = message.contact
    raw_phone = contact.phone_number.strip().replace(' ', '').replace('-', '')
    if not raw_phone.startswith('+'):
        raw_phone = '+' + raw_phone

    with flask_app.app_context():
        # Mijoz bazada mavjudmi tekshirish
        client = Client.query.filter_by(phone=raw_phone).first()

        if not client:
            # Yangi mijoz yaratish
            full_name = f"{contact.first_name or ''} {contact.last_name or ''}".strip() or "Mijoz"
            qr_token = Client.generate_unique_qr_code()

            client = Client(
                full_name=full_name,
                phone=raw_phone,
                qr_code=qr_token,
                status='active',
                notes="Telegram bot orqali ro'yxatdan o'tdi"
            )
            db.session.add(client)
            db.session.flush()

            # QR rasmini yaratish
            qr_img_name = f"qr_{client.id}_{qr_token}.png"
            qr_img_path = os.path.join(Config.QRCODES_FOLDER, qr_img_name)
            generate_qr_code_image(qr_token, qr_img_path)

            qr_rec = ClientQRCode(
                client_id=client.id,
                qr_code_token=qr_token,
                qr_image_path=f"qrcodes/{qr_img_name}",
                is_active=True
            )
            db.session.add(qr_rec)

        # Telegram foydalanuvchisi yozuvini yangilash yoki yaratish
        tg_user = TelegramUser.query.filter_by(telegram_id=message.from_user.id).first()
        if not tg_user:
            tg_user = TelegramUser(
                client_id=client.id,
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                phone_number=raw_phone,
                step='registered',
                is_active=True
            )
            db.session.add(tg_user)
        else:
            tg_user.client_id = client.id
            tg_user.phone_number = raw_phone
            tg_user.username = message.from_user.username

        db.session.commit()

        await message.answer(
            f"✅ Rahmat, <b>{client.full_name}</b>!\n\n"
            f"Telefon raqamingiz muvaffaqiyatli tasdiqlandi va profilingiz tizimga bog'landi.\n"
            f"Sizning shaxsiy QR identifikatoringiz: <code>{client.qr_code}</code>\n\n"
            f"Endi zaldan foydalanish uchun quyidagi menyuni tanlang:",
            reply_markup=get_main_menu(),
            parse_mode="HTML"
        )
