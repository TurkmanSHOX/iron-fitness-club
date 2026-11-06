import os
import socket
import logging
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

logger = logging.getLogger("IronFitnessConfig")

def check_mariadb_connection(uri):
    """MariaDB/MySQL serveri ishlayotganini tezkor tekshirish"""
    if not uri or 'mysql' not in uri:
        return False
    try:
        # Host va portni ajratib olish: mysql+pymysql://user:pass@host:port/dbname
        host_port = uri.split('@')[1].split('/')[0]
        if ':' in host_port:
            host, port_str = host_port.split(':')
            port = int(port_str)
        else:
            host = host_port
            port = 3306

        with socket.create_connection((host, port), timeout=1.0):
            return True
    except Exception:
        return False

def get_database_uri():
    """
    MariaDB asosiy baza sifatida o'rnatiladi.
    Production rejimida MariaDB ishlamasa, dastur ishga tushishni qat'iy rad etadi.
    """
    raw_db_url = os.environ.get('DATABASE_URL', '')
    env_mode = os.environ.get('FLASK_ENV', os.environ.get('ENVIRONMENT', 'development')).lower()
    is_prod = env_mode in ['production', 'prod']
    is_testing = os.environ.get('TESTING', 'false').lower() == 'true'

    if is_testing:
        return 'sqlite:///:memory:'

    if 'mysql' in raw_db_url:
        if check_mariadb_connection(raw_db_url):
            return raw_db_url
        else:
            if is_prod:
                raise RuntimeError(
                    "\n====================================================================\n"
                    "FATAL ERROR: MariaDB ma'lumotlar bazasiga ulanib bo'lmadi!\n"
                    "Talab: Ishlab chiqarish (Production) rejimida MariaDB serveri\n"
                    "(localhost:3306) ishlab turishi SHART. SQLite bazasidan foydalanish\n"
                    "qat'iyan taqiqlangan.\n\n"
                    "Iltimos, quyidagilarni bajaring:\n"
                    "1. MariaDB/MySQL xizmati ishga tushirilganligini tekshiring (mysqld / service mariadb start)\n"
                    "2. .env faylidagi DATABASE_URL parametrini to'g'ri sozlang (mysql+pymysql://user:pass@localhost:3306/iron_fitness_club)\n"
                    "====================================================================\n"
                )
            else:
                logger.warning(
                    "[DIQQAT] MariaDB serveri (localhost:3306) ulanmadi! "
                    "Dastur faqat lokal ishlab chiqish (Development) rejimida bo'lgani uchun "
                    "vaqtinchalik SQLite rejimida ishlayapti. MariaDB ni ishga tushiring."
                )
                db_path = os.path.join(BASE_DIR, 'instance', 'iron_fitness.db')
                return f"sqlite:///{db_path}"

    if is_prod:
        raise RuntimeError(
            "\n====================================================================\n"
            "FATAL ERROR: DATABASE_URL sozlanmagan yoki MariaDB manzili ko'rsatilmagan!\n"
            "Production rejimida MariaDB bo'lishi shart.\n"
            "====================================================================\n"
        )

    db_path = os.path.join(BASE_DIR, 'instance', 'iron_fitness.db')
    return f"sqlite:///{db_path}"

class Config:
    """IRON FITNESS CLUB - Asosiy tizim konfiguratsiyasi"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'iron-fitness-secret-key-2026-production')
    
    # Ma'lumotlar bazasi: MariaDB (HeidiSQL mos)
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 280,
        'pool_pre_ping': True,
    }

    # Vaqt mintaqasi
    TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Tashkent')

    # CSRF himoyasi
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 86400  # 24 soat

    # Sessiya xavfsizligi
    PERMANENT_SESSION_LIFETIME = timedelta(hours=14)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'

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
