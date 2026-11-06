from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_contact_keyboard():
    """Ro'yxatdan o'tish uchun telefon raqamini yuborish tugmasi"""
    kb = [
        [KeyboardButton(text="📱 Telefon raqamimni yuborish", request_contact=True)]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True, one_time_keyboard=True)


def get_main_menu():
    """Mijoz uchun asosiy menyu klaviaturasi"""
    kb = [
        [KeyboardButton(text="🎫 Mening abonementim"), KeyboardButton(text="📱 Mening QR-kodim")],
        [KeyboardButton(text="💳 Abonement xarid qilish"), KeyboardButton(text="❄️ Muzlatish so'rovi")],
        [KeyboardButton(text="🕒 Tashriflar tarixi"), KeyboardButton(text="🧾 To'lovlar tarixi")],
        [KeyboardButton(text="🎁 Aksiyalar"), KeyboardButton(text="📞 Administrator bilan aloqa")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
