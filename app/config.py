import os
import logging
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

logger = logging.getLogger("IronFitnessConfig")

INSECURE_SECRET_KEYS = {
    'iron-fitness-dev-key-change-in-prod-2026',
    'iron-fitness-secret-key-2026-production',
    'iron-fitness-super-secret-key-2026-production',
    'secret',
    'secret_key',
    'admin',
    'admin123',
    '123456',
    '12345678',
    'password',
    'changeme'
}

def get_secret_key():
    """
    SECRET_KEY ni xavfsiz olish va tekshirish.
    Production rejimida SECRET_KEY .env orqali berilmagan bo'lsa yoki
    standart/zaif bo'lsa, dastur ishga tushishni qat'iyan rad etadi.
    """
    env_mode = os.environ.get('FLASK_ENV', os.environ.get('ENVIRONMENT', 'development')).lower()
    is_prod = env_mode in ['production', 'prod']
    is_testing = os.environ.get('TESTING', 'false').lower() == 'true'

    raw_secret = os.environ.get('SECRET_KEY', '').strip()

    if is_testing:
        return raw_secret or 'iron-fitness-test-secret-key-32chars-min'

    if is_prod:
        if not raw_secret:
            raise RuntimeError(
                "\n====================================================================\n"
                "XAVFSIZLIK XATOLIGI: SECRET_KEY .env faylida ko'rsatilmagan!\n"
                "Ishlab chiqarish (Production) rejimida dastur maxfiy kalitsiz ishga tusha olmaydi.\n"
                "Iltimos, .env faylida kamida 32 belgidan iborat tasodifiy kuchli SECRET_KEY belgilang.\n"
                "====================================================================\n"
            )
        if (raw_secret.lower() in INSECURE_SECRET_KEYS or 
            len(raw_secret) < 32 or 
            'change-in-prod' in raw_secret.lower() or 
            'super-secret-key' in raw_secret.lower()):
            raise RuntimeError(
                "\n====================================================================\n"
                "XAVFSIZLIK XATOLIGI: Standart yoki zaif SECRET_KEY aniqlandi!\n"
                f"Kiritilgan kalit zaif yoki shablon qiymat bo'lgani sababli ishlab chiqarishda rad etildi.\n"
                "Talab: Kamida 32 ta belgidan iborat, xavfsiz generatsiya qilingan kriptografik kalitdan foydalaning.\n"
                "====================================================================\n"
            )
        return raw_secret

    # Development rejimi
    if not raw_secret or raw_secret.lower() in INSECURE_SECRET_KEYS:
        logger.warning(
            "[DIQQAT] .env faylida SECRET_KEY belgilanmagan yoki zaif kalit ishlatilmoqda. "
            "Lokal dasturlash uchun vaqtinchalik kalit ishlatilmoqda. Ishlab chiqarishda buni almashtiring!"
        )
        return 'iron-fitness-development-temporary-key-only-for-local-dev'

    return raw_secret

def check_mariadb_connection(uri):
    """
    MariaDB/MySQL serveri ishlayotganini haqiqiy SQL so'rovi (SELECT 1) orqali tekshirish.
    Faqat port ochilganligi bilan cheklanmaydi.
    """
    if not uri or 'mysql' not in uri:
        return False
    try:
        engine = create_engine(
            uri,
            connect_args={'connect_timeout': 2},
            pool_pre_ping=True
        )
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            return result == 1
    except Exception as e:
        logger.debug(f"MariaDB SQL ulanish xatosi: {e}")
        return False

def get_database_uri():
    """
    MariaDB asosiy baza sifatida o'rnatiladi.
    Production rejimida MariaDB ishlamasa, dastur ishga tushishni qat'iy rad etadi.
    Production rejimida SQLite fallback mutlaqo yo'q.
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
                    "SQLAlchemy orqali 'SELECT 1' tekshiruv so'rovi bajarilmadi.\n"
                    "Talab: Ishlab chiqarish (Production) rejimida MariaDB serveri\n"
                    "(localhost:3306) ishlab turishi SHART. SQLite bazasidan foydalanish\n"
                    "mutlaqo taqiqlangan.\n\n"
                    "Iltimos, quyidagilarni bajaring:\n"
                    "1. MariaDB/MySQL xizmati ishga tushirilganligini tekshiring (mysqld / service mariadb start)\n"
                    "2. .env faylidagi DATABASE_URL parametrini to'g'ri sozlang (mysql+pymysql://user:pass@localhost:3306/iron_fitness_club)\n"
                    "====================================================================\n"
                )
            else:
                logger.warning(
                    "[DIQQAT] MariaDB serveri (localhost:3306) ulanmadi yoki SELECT 1 bajarilmadi! "
                    "Dastur faqat lokal ishlab chiqish (Development) rejimida bo'lgani uchun "
                    "vaqtinchalik SQLite rejimida ishlayapti. MariaDB ni ishga tushiring."
                )
                db_path = os.path.join(BASE_DIR, 'instance', 'iron_fitness.db')
                return f"sqlite:///{db_path}"

    if is_prod:
        raise RuntimeError(
            "\n====================================================================\n"
            "FATAL ERROR: DATABASE_URL sozlanmagan yoki MariaDB manzili ko'rsatilmagan!\n"
            "Production rejimida MariaDB bo'lishi shart. SQLite fallback ruxsat etilmaydi.\n"
            "====================================================================\n"
        )

    db_path = os.path.join(BASE_DIR, 'instance', 'iron_fitness.db')
    return f"sqlite:///{db_path}"

class Config:
    """IRON FITNESS CLUB - Asosiy tizim konfiguratsiyasi"""
    SECRET_KEY = get_secret_key()
    
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
