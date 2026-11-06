from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_tariffs_keyboard(tariffs):
    """Tariflar ro'yxatini inline tugmalar sifatida chiqarish"""
    buttons = []
    for t in tariffs:
        buttons.append([
            InlineKeyboardButton(
                text=f"{t.name} - {int(t.price):,} so'm".replace(',', ' '),
                callback_data=f"buy_tariff:{t.id}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_payment_keyboard(tariff_id, amount):
    """Click va Payme to'lov usullari inline tugmalari"""
    buttons = [
        [
            InlineKeyboardButton(text="🔹 Click orqali to'lash", callback_data=f"pay_click:{tariff_id}"),
            InlineKeyboardButton(text="🔹 Payme orqali to'lash", callback_data=f"pay_payme:{tariff_id}")
        ],
        [
            InlineKeyboardButton(text="💵 Zalda naqd/karta bilan to'lash", callback_data=f"pay_offline:{tariff_id}")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_payment")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
