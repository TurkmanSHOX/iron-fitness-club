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
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'

    print("=" * 65)
    print("      IRON FITNESS CLUB - AVTOMATLASHTIRISH TIZIMI")
    print("=" * 65)
    print(f" * Veb-panel manzili:  http://{host}:{port}")
    print(f" * Standart Admin:     Login: admin | Parol: admin123")
    print(f" * Ma'lumotlar bazasi: {Config.SQLALCHEMY_DATABASE_URI}")
    print(f" * Vaqt mintaqasi:     {Config.TIMEZONE}")
    print("=" * 65)

    app.run(host=host, port=port, debug=debug)
