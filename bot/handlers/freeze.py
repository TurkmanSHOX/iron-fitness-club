from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.models.client import TelegramUser
from app.models.setting import Setting
from app.services.freeze_service import create_freeze_request

freeze_router = Router()

class FreezeState(StatesGroup):
    waiting_for_days = State()
    waiting_for_reason = State()

@freeze_router.message(F.text == "❄️ Muzlatish so'rovi")
async def start_freeze_flow(message: Message, state: FSMContext, flask_app):
    """Muzlatish so'rovini boshlash"""
    with flask_app.app_context():
        tg_user = TelegramUser.query.filter_by(telegram_id=message.from_user.id).first()
        if not tg_user or not tg_user.client_id:
            await message.answer("Iltimos, avval telefon raqamingizni yuborib ro'yxatdan o'ting.")
            return

        client = tg_user.client
        sub = client.active_subscription

        if not sub or sub.status != 'active':
            await message.answer("Sizda ayni paytda faol holatdagi abonement mavjud emas.")
            return

        max_days = Setting.get_value('max_freeze_days', '10')

        await state.set_state(FreezeState.waiting_for_days)
        await message.answer(
            f"❄️ <b>Abonementni vaqtincha muzlatish</b>\n\n"
            f"Amaldagi qoidaga ko'ra, siz ko'pi bilan <b>{max_days} kunga</b> muzlatish so'rashingiz mumkin.\n\n"
            f"Abonementingizni necha kunga muzlatmoqchisiz? (Faqat son kiriting, masalan: 5):",
            parse_mode="HTML"
        )


@freeze_router.message(FreezeState.waiting_for_days)
async def process_freeze_days(message: Message, state: FSMContext, flask_app):
    text = message.text.strip()
    if not text.isdigit():
        await message.answer("Iltimos, faqat musbat son kiriting (masalan: 3, 5, 7):")
        return

    days = int(text)
    with flask_app.app_context():
        max_days = int(Setting.get_value('max_freeze_days', '10'))
        if days <= 0 or days > max_days:
            await message.answer(f"Kunlar soni 1 dan {max_days} gacha bo'lishi kerak. Qayta kiriting:")
            return

    await state.update_data(freeze_days=days)
    await state.set_state(FreezeState.waiting_for_reason)
    await message.answer(
        "Muzlatish sababini yozing (masalan: Xizmat safari, betoblik, ta'til):"
    )


@freeze_router.message(FreezeState.waiting_for_reason)
async def process_freeze_reason(message: Message, state: FSMContext, flask_app):
    reason = message.text.strip()
    data = await state.get_data()
    days = data.get('freeze_days')

    with flask_app.app_context():
        tg_user = TelegramUser.query.filter_by(telegram_id=message.from_user.id).first()
        client = tg_user.client

        success, res = create_freeze_request(
            client_id=client.id,
            days_count=days,
            reason=reason
        )

        await state.clear()

        if success:
            await message.answer(
                f"✅ <b>Muzlatish so'rovingiz qabul qilindi!</b>\n\n"
                f"⏱ So'ralgan muddat: <b>{days} kun</b>\n"
                f"📝 Sabab: <i>{reason}</i>\n\n"
                f"Administrator so'rovingizni ko'rib chiqib tasdiqlagach, sizga xabar yuboriladi.",
                parse_mode="HTML"
            )
        else:
            await message.answer(f"❌ Xatolik: {res}")
