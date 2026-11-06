import os
import sys
import gzip
import shutil
import subprocess

# Loyiha ildiz katalogini Python path ga kiritish
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from app.config import Config, check_mariadb_connection
from app.extensions import db
from app.models.setting import AuditLog
from scripts.backup import parse_database_url

def restore_backup(backup_file_path):
    """
    Zaxira faylidan ma'lumotlar bazasini qayta tiklash.
    MariaDB bo'lsa `mysql` buyrug'i orqali import qiladi.
    Lokal SQLite bo'lsa `.db` faylini almashtiradi.
    """
    if not os.path.exists(backup_file_path):
        print(f"[ERROR] Zaxira fayli topilmadi: {backup_file_path}")
        return False, "Fayl topilmadi"

    app = create_app()
    with app.app_context():
        raw_db_url = os.environ.get('DATABASE_URL', '')
        parsed = parse_database_url(raw_db_url)
        is_mariadb_active = check_mariadb_connection(raw_db_url)

        if parsed and is_mariadb_active:
            # Agar arxivlangan (.gz) bo'lsa, vaqtinchalik ochish
            temp_sql = None
            if backup_file_path.endswith('.gz'):
                temp_sql = backup_file_path[:-3]
                with gzip.open(backup_file_path, 'rb') as f_in, open(temp_sql, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                target_sql = temp_sql
            else:
                target_sql = backup_file_path

            cmd = [
                'mysql',
                f"-h{parsed['host']}",
                f"-P{parsed['port']}",
                f"-u{parsed['user']}",
                '--default-character-set=utf8mb4',
                parsed['dbname']
            ]
            if parsed['password']:
                cmd.insert(4, f"-p{parsed['password']}")

            try:
                with open(target_sql, 'r', encoding='utf-8') as f:
                    subprocess.run(cmd, stdin=f, check=True)

                if temp_sql and os.path.exists(temp_sql):
                    os.remove(temp_sql)

                AuditLog.log(
                    action='DATABASE_RESTORED',
                    admin_id=None,
                    details=f"MariaDB bazasi zaxiradan tiklandi: {os.path.basename(backup_file_path)}"
                )
                print(f"[SUCCESS] MariaDB muvaffaqiyatli tiklandi: {backup_file_path}")
                return True, "MariaDB tiklandi"

            except Exception as e:
                if temp_sql and os.path.exists(temp_sql):
                    os.remove(temp_sql)
                err_msg = f"MariaDB tiklashda xatolik: {e}"
                print(f"[ERROR] {err_msg}")
                return False, err_msg
        else:
            # SQLite tiklash
            dest_db = os.path.join(BASE_DIR, 'instance', 'iron_fitness.db')
            shutil.copy2(backup_file_path, dest_db)
            print(f"[SUCCESS] Lokal SQLite bazasi tiklandi: {dest_db}")
            return True, "SQLite tiklandi"

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Foydalanish: python scripts/restore.py <zaxira_fayli_yo'li>")
        sys.exit(1)

    restore_backup(sys.argv[1])
