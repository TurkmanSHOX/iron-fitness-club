import os
import sys

# Windows terminalida UTF-8 ni qo'llab-quvvatlash
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app import create_app
from app.config import Config

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    # Development va Production rejimlarini qat'iy ajratish
    env_mode = os.environ.get('FLASK_ENV', os.environ.get('ENVIRONMENT', 'development')).lower()
    is_prod = env_mode in ['production', 'prod']

    if is_prod:
        debug = False
        mode_label = "PRODUCTION (Ishlab chiqarish - Xavfsiz rejim)"
    else:
        debug = os.environ.get('DEBUG', 'True').lower() == 'true'
        mode_label = "DEVELOPMENT (Lokal dasturlash va sinov)"

    print("=" * 65)
    print("      IRON FITNESS CLUB - AVTOMATLASHTIRISH TIZIMI")
    print("=" * 65)
    print(f" * Rejim:              {mode_label}")
    print(f" * Debug holati:       {debug}")
    print(f" * Veb-panel manzili:  http://{host}:{port}")
    print(f" * Ma'lumotlar bazasi: {Config.SQLALCHEMY_DATABASE_URI}")
    print(f" * Vaqt mintaqasi:     {Config.TIMEZONE}")
    print(" * Xavfsizlik:         Dastlabki kirishda parol majburiy almashtiriladi")
    if is_prod:
        print(" [OGOHLANTIRISH] Production rejimida WSGI serveri (wsgi.py / Waitress / Gunicorn) tavsiya etiladi.")
    print("=" * 65)

    app.run(host=host, port=port, debug=debug)
