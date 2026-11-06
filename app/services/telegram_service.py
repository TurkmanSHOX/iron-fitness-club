import os
import requests
from app.config import Config
from app.models.setting import Setting

def get_bot_token():
    return Config.TELEGRAM_BOT_TOKEN or Setting.get_value('telegram_bot_token', '')

def send_telegram_message(telegram_id, text, parse_mode='HTML'):
    """Telegram bot orqali foydalanuvchiga matnli xabar yuborish"""
    token = get_bot_token()
    if not token or not telegram_id:
        return False, "Bot token yoki Telegram ID kiritilmagan"

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': telegram_id,
        'text': text,
        'parse_mode': parse_mode
    }
    try:
        resp = requests.post(url, json=payload, timeout=8)
        data = resp.json()
        if data.get('ok'):
            return True, data
        return False, data.get('description', 'Telegram API xatoligi')
    except Exception as e:
        return False, str(e)


def send_telegram_photo(telegram_id, photo_path, caption=None):
    """Telegram bot orqali rasm yuborish (masalan: shaxsiy QR-kod)"""
    token = get_bot_token()
    if not token or not telegram_id or not os.path.exists(photo_path):
        return False, "Fayl topilmadi yoki token yo'q"

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    data = {'chat_id': telegram_id}
    if caption:
        data['caption'] = caption
        data['parse_mode'] = 'HTML'

    try:
        with open(photo_path, 'rb') as f:
            files = {'photo': f}
            resp = requests.post(url, data=data, files=files, timeout=15)
            res_data = resp.json()
            if res_data.get('ok'):
                return True, res_data
            return False, res_data.get('description', 'Telegram xatoligi')
    except Exception as e:
        return False, str(e)


def send_telegram_document(telegram_id, doc_path, caption=None):
    """Telegram bot orqali hujjat/PDF chek yuborish"""
    token = get_bot_token()
    if not token or not telegram_id or not os.path.exists(doc_path):
        return False, "Fayl topilmadi yoki token yo'q"

    url = f"https://api.telegram.org/bot{token}/sendDocument"
    data = {'chat_id': telegram_id}
    if caption:
        data['caption'] = caption
        data['parse_mode'] = 'HTML'

    try:
        with open(doc_path, 'rb') as f:
            files = {'document': f}
            resp = requests.post(url, data=data, files=files, timeout=15)
            res_data = resp.json()
            if res_data.get('ok'):
                return True, res_data
            return False, res_data.get('description', 'Telegram xatoligi')
    except Exception as e:
        return False, str(e)
