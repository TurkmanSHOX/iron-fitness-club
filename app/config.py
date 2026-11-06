import os
import socket
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

def _check_db_connection(uri):
    """MariaDB/MySQL serveri ishlayotganini tezkor tekshirish"""
    if not uri or 'mysql' not in uri:
        return uri
    try:
        # Host va portni ajratib olish: mysql+pymysql://user:pass@host:port/dbname
        host_port = uri.split('@')[1].split('/')[0]
        if ':' in host_port:
            host, port_str = host_port.split(':')
            port = int(port_str)
        else:
            host = host_port
            port = 3306

        with socket.create_connection((host, port), timeout=0.8):
            return uri
    except Exception:
        # MariaDB ulanmasa lokal SQLite ga fallback
        return None

class Config:
    """IRON FITNESS CLUB - Asosiy tizim konfiguratsiyasi"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'iron-fitness-dev-key-change-in-prod-2026')
    
    # Ma'lumotlar bazasi: MariaDB (HeidiSQL)
    _raw_db_url = os.environ.get('DATABASE_URL')
    _active_db_url = _check_db_connection(_raw_db_url)
    
    if _active_db_url:
        SQLALCHEMY_DATABASE_URI = _active_db_url
    else:
        db_path = os.path.join(BASE_DIR, 'instance', 'iron_fitness.db')
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    # Vaqt mintaqasi
    TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Tashkent')

    # Sessiya xavfsizligi
    PERMANENT_SESSION_LIFETIME = timedelta(hours=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False  # HTTPS serverda True qilinadi

    # Fayl yuklash kataloglari
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}

    # Hisobot va chek kataloglari
    REPORTS_FOLDER = os.path.join(BASE_DIR, 'reports')
    RECEIPTS_FOLDER = os.path.join(BASE_DIR, 'uploads', 'receipts')
    QRCODES_FOLDER = os.path.join(BASE_DIR, 'uploads', 'qrcodes')
    BACKUPS_FOLDER = os.path.join(BASE_DIR, 'backups')

    # Telegram Bot
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_BOT_USERNAME = os.environ.get('TELEGRAM_BOT_USERNAME', 'iron_fitness_club_bot')
    ADMIN_TELEGRAM_ID = os.environ.get('ADMIN_TELEGRAM_ID', '')

    # Click & Payme
    CLICK_MERCHANT_ID = os.environ.get('CLICK_MERCHANT_ID', '')
    CLICK_SERVICE_ID = os.environ.get('CLICK_SERVICE_ID', '')
    CLICK_SECRET_KEY = os.environ.get('CLICK_SECRET_KEY', '')

    PAYME_MERCHANT_ID = os.environ.get('PAYME_MERCHANT_ID', '')
    PAYME_SECRET_KEY = os.environ.get('PAYME_SECRET_KEY', '')
    PAYME_TEST_MODE = os.environ.get('PAYME_TEST_MODE', 'true').lower() == 'true'
