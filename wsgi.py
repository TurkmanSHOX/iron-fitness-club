import os
import sys
import logging

# Loyiha ildiz katalogini Python path ga kiritish
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger('IronFitnessWSGI')

from app import create_app

# WSGI Application ob'ekti (Gunicorn / uWSGI / Waitress uchun)
app = create_app()

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    threads = int(os.environ.get('WSGI_THREADS', 8))

    logger.info(f"IRON FITNESS CLUB Production WSGI Server ishga tushmoqda: http://{host}:{port} (Threads: {threads})")
    
    try:
        from waitress import serve
        serve(app, host=host, port=port, threads=threads)
    except ImportError:
        logger.warning("Waitress topilmadi, standart WSGI rejimida ishga tushirilmoqda.")
        app.run(host=host, port=port, debug=False)
