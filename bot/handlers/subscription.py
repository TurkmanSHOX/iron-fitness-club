from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from bot.keyboards.inline import get_tariffs_keyboard, get_payment_keyboard
from app.extensions import db
from app.models.client import TelegramUser, Client
from app.models.tariff import Tariff
from app.models.subscription import Subscription
from app.services.subscription_service import create_subscription

sub_router = Router()

@sub_router.message(F.text == "🎫 Mening abonementim")
async def my_subscription(message: Message, flask_app):
    """Mijozning joriy abonement ma'lumotlarini ko'rsatish"""
    with flask_app.app_context():
        tg_user = TelegramUser.query.filter_by(telegram_id=message.from_user.id).first()
        if not tg_user or not tg_user.client_id:
            await message.answer("Iltimos, avval telefon raqamingizni yuborib ro'yxatdan o'ting.")
            return

        client = tg_user.client
        sub = client.active_subscription

        if not sub:
            await message.answer(
                f"Hurmatli <b>{client.full_name}</b>!\n\n"
                f"Sizda hozirda faol abonement mavjud emas.\n"
                f"Yangi abonement xarid qilish uchun <b>«💳 Abonement xarid qilish»</b> tugmasini bosing.",
                parse_mode="HTML"
            )
            return

        status_text = {
            'active': '✅ Faol',
            'frozen': '❄️ Muzlatilgan',
            'expired': '🛑 Muddati tugagan'
        }.get(sub.status, sub.status)

        text = (
            f"🎫 <b>Sizning Abonementingiz:</b>\n\n"
            f"Tarif: <b>{sub.tariff.name}</b>\n"
            f"Turi: <i>{sub.tariff.type_label}</i>\n"
            f"Boshlanish sanasi: <b>{sub.start_date.strftime('%d.%m.%Y')}</b>\n"
            f"Tugash sanasi: <b>{sub.end_date.strftime('%d.%m.%Y')}</b>\n"
            f"Qolgan kunlar: <b>{sub.days_left} kun</b>\n"
            f"Holati: <b>{status_text}</b>\n\n"
            f"To'langan summa: {int(sub.paid_amount):,} so'm\n"
            f"QR identifikatoringiz: <code>{client.qr_code}</code>"
        ).replace(',', ' ')

        await message.answer(text, parse_mode="HTML")


@sub_router.message(F.text == "💳 Abonement xarid qilish")
async def buy_subscription(message: Message, flask_app):
    """Abonement xarid qilish uchun amaldagi tariflarni chiqarish"""
    with flask_app.app_context():
        tariffs = Tariff.query.filter_by(is_active=True).all()
        if not tariffs:
            await message.answer("Hozirda sotuvda tariflar mavjud emas.")
            return

        await message.answer(
            "Quyidagi amaldagi tariflardan birini tanlang:",
            reply_markup=get_tariffs_keyboard(tariffs)
        )


@sub_router.callback_query(F.data.startswith("buy_tariff:"))
async def select_tariff_callback(callback: CallbackQuery, flask_app):
    """Tarif tanlanganda to'lov usullarini ko'rsatish"""
    tariff_id = int(callback.data.split(":")[1])
    with flask_app.app_context():
        tariff = Tariff.query.get(tariff_id)
        if not tariff:
            await callback.answer("Tarif topilmadi!", show_alert=True)
            return

        price_formatted = f"{int(tariff.price):,} so'm".replace(',', ' ')
        text = (
            f"📌 <b>Tanlangan tarif:</b> {tariff.name}\n"
            f"⏱ <b>Amal qilish muddati:</b> {tariff.duration_days} kun\n"
            f"💵 <b>To'lov summasi:</b> {price_formatted}\n\n"
            f"Foydalanish tartibi: <i>{tariff.type_label}</i>\n\n"
            f"To'lov turini tanlang:"
        )

        await callback.message.edit_text(
            text,
            reply_markup=get_payment_keyboard(tariff.id, tariff.price),
            parse_mode="HTML"
        )
        await callback.answer()


@sub_router.callback_query(F.data.startswith("pay_offline:"))
async def pay_offline_callback(callback: CallbackQuery, flask_app):
    """Reception orqali to'lash tanlanganda"""
    tariff_id = int(callback.data.split(":")[1])
    with flask_app.app_context():
        tariff = Tariff.query.get(tariff_id)
        await callback.message.edit_text(
            f"✅ <b>Buyurtmangiz qabul qilindi!</b>\n\n"
            f"Tarif: <b>{tariff.name}</b>\n"
            f"Summa: <b>{int(tariff.price):,} so'm</b>\n\n"
            f"Zalga tashrif buyurganingizda reception administratoriga naqd pul yoki bank kartasi orqali to'lov qilib, abonementingizni faollashtirib olishingiz mumkin.\n"
            f"QR-kodingiz: profilingizda saqlangan.".replace(',', ' '),
            parse_mode="HTML"
        )
        await callback.answer()


@sub_router.callback_query(F.data.startswith("pay_click:") | F.data.startswith("pay_payme:"))
async def pay_online_callback(callback: CallbackQuery, flask_app):
    """Click yoki Payme to'lov havolasini taqdim etish"""
    provider = "Click" if "click" in callback.data else "Payme"
    tariff_id = int(callback.data.split(":")[1])
    
    with flask_app.app_context():
        tg_user = TelegramUser.query.filter_by(telegram_id=callback.from_user.id).first()
        tariff = Tariff.query.get(tariff_id)
        
        # Click / Payme havola shabloni
        merchant_trans_id = f"client_{tg_user.client_id}_tariff_{tariff.id}"
        amount = int(tariff.price)

        await callback.message.edit_text(
            f"💳 <b>{provider} orqali to'lov</b>\n\n"
            f"Tarif: <b>{tariff.name}</b>\n"
            f"To'lov summasi: <b>{amount:,} so'm</b>\n\n"
            f"To'lov tizimiga yo'naltiruvchi havola:\n"
            f"🔗 <a href='https://my.click.uz'>To'lovni amalga oshirish ({provider})</a>\n\n"
            f"To'lov tasdiqlangach abonementingiz avtomatik ravishda faollashadi va bot sizga xabar beradi!".replace(',', ' '),
            parse_mode="HTML"
        )
        await callback.answer()


@sub_router.callback_query(F.data == "cancel_payment")
async def cancel_payment_callback(callback: CallbackQuery):
    await callback.message.edit_text("To'lov bekor qilindi.")
    await callback.answer()
