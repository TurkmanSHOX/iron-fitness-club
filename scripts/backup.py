import os
import sys
import gzip
import shutil
import subprocess
from datetime import datetime

# Loyiha ildiz katalogini Python path ga kiritish
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from app.config import Config, check_mariadb_connection
from app.extensions import db
from app.models.setting import BackupLog, AuditLog

def parse_database_url(url):
    """mysql+pymysql://user:pass@host:port/dbname formatidan parametrlarni ajratish"""
    if not url or 'mysql' not in url:
        return None
    try:
        # mysql+pymysql://user:pass@host:port/dbname?charset=utf8mb4
        clean = url.split('://')[1].split('?')[0]
        user_pass, host_db = clean.split('@')
        if ':' in user_pass:
            user, password = user_pass.split(':', 1)
        else:
            user = user_pass
            password = ''

        host_port, dbname = host_db.split('/', 1)
        if ':' in host_port:
            host, port = host_port.split(':', 1)
        else:
            host = host_port
            port = '3306'

        return {
            'user': user,
            'password': password,
            'host': host,
            'port': port,
            'dbname': dbname
        }
    except Exception as e:
        print(f"DATABASE_URL parse xatosi: {e}")
        return None

def make_backup(backup_type='manual', compress=True):
    """
    MariaDB / MySQL ma'lumotlar bazasini zaxiralash (mysqldump).
    Lokal SQLite bo'lsa, fayldan nusxa oladi.
    """
    app = create_app()
    with app.app_context():
        os.makedirs(Config.BACKUPS_FOLDER, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        raw_db_url = os.environ.get('DATABASE_URL', '')
        parsed = parse_database_url(raw_db_url)
        is_mariadb_active = check_mariadb_connection(raw_db_url)

        if parsed and is_mariadb_active:
            # MariaDB mysqldump
            sql_filename = f"backup_{parsed['dbname']}_{timestamp}.sql"
            sql_filepath = os.path.join(Config.BACKUPS_FOLDER, sql_filename)

            cmd = [
                'mysqldump',
                f"-h{parsed['host']}",
                f"-P{parsed['port']}",
                f"-u{parsed['user']}",
                '--single-transaction',
                '--quick',
                '--default-character-set=utf8mb4',
                parsed['dbname']
            ]
            if parsed['password']:
                cmd.insert(4, f"-p{parsed['password']}")

            try:
                with open(sql_filepath, 'w', encoding='utf-8') as f:
                    proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, check=True)

                final_filepath = sql_filepath
                final_filename = sql_filename

                if compress:
                    gz_filename = f"{sql_filename}.gz"
                    gz_filepath = os.path.join(Config.BACKUPS_FOLDER, gz_filename)
                    with open(sql_filepath, 'rb') as f_in, gzip.open(gz_filepath, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    os.remove(sql_filepath)
                    final_filepath = gz_filepath
                    final_filename = gz_filename

                file_size = os.path.getsize(final_filepath)
                log = BackupLog(
                    file_name=final_filename,
                    file_size=file_size,
                    backup_type=backup_type,
                    status='success',
                    message="MariaDB mysqldump muvaffaqiyatli bajarildi"
                )
                db.session.add(log)
                db.session.commit()
                print(f"[SUCCESS] MariaDB zaxira nusxasi yaratildi: {final_filename} ({file_size} bayt)")
                return True, final_filepath

            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                err_msg = f"mysqldump bajarishda xatolik: {e}"
                print(f"[ERROR] {err_msg}")
                log = BackupLog(
                    file_name=sql_filename,
                    file_size=0,
                    backup_type=backup_type,
                    status='failed',
                    message=err_msg
                )
                db.session.add(log)
                db.session.commit()
                return False, err_msg
        else:
            # SQLite dev zaxirasi
            sqlite_db = os.path.join(BASE_DIR, 'instance', 'iron_fitness.db')
            if not os.path.exists(sqlite_db):
                return False, "Baza fayli topilmadi"

            backup_filename = f"backup_sqlite_{timestamp}.db"
            backup_filepath = os.path.join(Config.BACKUPS_FOLDER, backup_filename)
            shutil.copy2(sqlite_db, backup_filepath)
            file_size = os.path.getsize(backup_filepath)

            log = BackupLog(
                file_name=backup_filename,
                file_size=file_size,
                backup_type=backup_type,
                status='success',
                message="Lokal SQLite zaxira nusxasi saqlandi"
            )
            db.session.add(log)
            db.session.commit()
            print(f"[SUCCESS] Lokal SQLite zaxira nusxasi yaratildi: {backup_filename} ({file_size} bayt)")
            return True, backup_filepath

if __name__ == '__main__':
    b_type = 'manual'
    if len(sys.argv) > 1:
        b_type = sys.argv[1]
    make_backup(backup_type=b_type)
