from aiogram import Router, F
from aiogram.types import Message
from app.models.client import TelegramUser
from app.models.visit import Visit
from app.models.payment import Payment
from app.models.promotion import Promotion
from app.models.setting import Setting

history_router = Router()

@history_router.message(F.text == "🕒 Tashriflar tarixi")
async def show_visits_history(message: Message, flask_app):
    """Mijozning so'nggi tashriflari"""
    with flask_app.app_context():
        tg_user = TelegramUser.query.filter_by(telegram_id=message.from_user.id).first()
        if not tg_user or not tg_user.client_id:
            await message.answer("Iltimos, avval ro'yxatdan o'ting.")
            return

        visits = Visit.query.filter_by(client_id=tg_user.client_id).order_by(Visit.id.desc()).limit(7).all()
        if not visits:
            await message.answer("Sizda hali tashriflar tarixi mavjud emas.")
            return

        lines = ["🕒 <b>So'nggi tashriflaringiz:</b>\n"]
        for v in visits:
            status_icon = "✅" if v.status == 'allowed' else "❌"
            lines.append(f"{status_icon} <b>{v.formatted_date}</b> {v.formatted_time} - {v.notes or v.denial_reason or 'Kirish'}")

        await message.answer("\n".join(lines), parse_mode="HTML")


@history_router.message(F.text == "🧾 To'lovlar tarixi")
async def show_payments_history(message: Message, flask_app):
    """Mijozning to'lovlar tarixi"""
    with flask_app.app_context():
        tg_user = TelegramUser.query.filter_by(telegram_id=message.from_user.id).first()
        if not tg_user or not tg_user.client_id:
            await message.answer("Iltimos, avval ro'yxatdan o'ting.")
            return

        payments = Payment.query.filter_by(client_id=tg_user.client_id).order_by(Payment.id.desc()).limit(5).all()
        if not payments:
            await message.answer("Sizda hali to'lovlar tarixi mavjud emas.")
            return

        lines = ["🧾 <b>So'nggi to'lovlaringiz:</b>\n"]
        for p in payments:
            amount_str = f"{int(p.amount):,} so'm".replace(',', ' ')
            lines.append(
                f"💳 <b>{p.payment_number}</b>\n"
                f"Sana: {p.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"Summa: <b>{amount_str}</b> ({p.method_label})\n"
                f"Turi: {p.type_label}\n"
            )

        await message.answer("\n".join(lines), parse_mode="HTML")


@history_router.message(F.text == "🎁 Aksiyalar")
async def show_promotions(message: Message, flask_app):
    """Faol aksiyalar va chegirmalar"""
    with flask_app.app_context():
        promos = Promotion.query.filter_by(is_active=True).all()
        active_promos = [p for p in promos if p.is_currently_valid]

        if not active_promos:
            await message.answer("Hozirda faol aksiyalar mavjud emas. Tez kunda yangi aksiyalarimiz e'lon qilinadi!")
            return

        lines = ["🎁 <b>Aktiv Aksiyalar va Chegirmalar:</b>\n"]
        for p in active_promos:
            discount_str = f"-{int(p.discount_value)}%" if p.discount_type == 'percent' else f"-{int(p.discount_value):,} so'm".replace(',', ' ')
            code_obj = p.promo_codes.first()
            code_str = f"\nPromo-kod: <code>{code_obj.code}</code>" if code_obj else ""

            lines.append(
                f"🔥 <b>{p.title}</b>\n"
                f"Chegirma: <b>{discount_str}</b>\n"
                f"Muddat: {p.start_date.strftime('%d.%m')} dan {p.end_date.strftime('%d.%m.%Y')} gacha{code_str}\n"
                f"<i>{p.description or ''}</i>\n"
            )

        await message.answer("\n".join(lines), parse_mode="HTML")


@history_router.message(F.text == "📞 Administrator bilan aloqa")
async def show_contact_admin(message: Message, flask_app):
    """Klub ma'lumotlari va administrator bilan aloqa"""
    with flask_app.app_context():
        club_name = Setting.get_value('club_name', 'IRON FITNESS CLUB')
        club_phone = Setting.get_value('club_phone', '+998 90 123 45 67')
        club_address = Setting.get_value('club_address', 'Urganch shahri, Al-Xorazmiy ko\'chasi, 24-uy')

        text = (
            f"🏢 <b>{club_name}</b>\n\n"
            f"📍 <b>Manzil:</b> {club_address}\n"
            f"📞 <b>Telefon:</b> {club_phone}\n"
            f"🕒 <b>Ish vaqti:</b> Har kuni 07:00 dan 23:00 gacha\n\n"
            f"Savollaringiz yoki takliflaringiz bo'lsa, reception bilan bog'lanishingiz mumkin."
        )
        await message.answer(text, parse_mode="HTML")
