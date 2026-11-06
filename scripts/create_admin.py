import os
import sys
import getpass
import re

# Loyiha ildiz katalogini Python path ga kiritish
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from app.extensions import db
from app.models.admin import Admin
from werkzeug.security import generate_password_hash


def validate_password(password):
    """Parol xavfsizligini tekshirish"""
    if len(password) < 8:
        return False, "Parol kamida 8 ta belgidan iborat bo'lishi shart!"
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        return False, "Parol tarkibida ham harflar, ham raqamlar bo'lishi shart!"
    return True, ""


import argparse

def main():
    parser = argparse.ArgumentParser(description="IRON FITNESS CLUB — Yangi administrator yaratish")
    parser.add_argument('--username', help="Administrator login nomi")
    parser.add_argument('--name', help="Administrator to'liq ismi (F.I.O)")
    parser.add_argument('--phone', help="Telefon raqami")
    parser.add_argument('--password', help="Maxfiy parol (kamida 8 belgi)")
    args = parser.parse_args()

    print("=" * 65)
    echo_title = "IRON FITNESS CLUB — YANGI ADMINISTRATOR YARATISH"
    print(echo_title.center(65))
    print("=" * 65)
    print("Standart yoki ochiq matnli parollar ishlatilmaydi.")
    print("Parol scrypt xesh bilan xavfsiz saqlanadi.\n")

    app = create_app()
    with app.app_context():
        # 1. Login nomi
        if args.username:
            username = args.username.strip()
        else:
            while True:
                username = input("Administrator login nomi (masalan: bosh_admin): ").strip()
                if not username or len(username) < 3:
                    print("[XATO] Login kamida 3 ta belgidan iborat bo'lishi shart!")
                    continue
                existing = Admin.query.filter_by(username=username).first()
                if existing:
                    choice = input(f"[OGOHLANTIRISH] '{username}' nomli admin allaqachon mavjud. Parolini yangilaysizmi? (ha/yo'q): ").strip().lower()
                    if choice == 'ha':
                        break
                    else:
                        continue
                break

        # 2. To'liq ism
        if args.name:
            full_name = args.name.strip()
        else:
            full_name = input("Administratorning to'liq ismi (F.I.O): ").strip()
            if not full_name:
                full_name = "Administrator"

        # 3. Telefon raqami
        if args.phone:
            phone = args.phone.strip()
        else:
            phone = input("Telefon raqami (masalan: +998901234567): ").strip()
            if not phone:
                phone = "+998900000000"

        # 4. Maxfiy parol
        if args.password:
            pwd = args.password.strip()
            valid, msg = validate_password(pwd)
            if not valid:
                print(f"[XATO] {msg}")
                sys.exit(1)
        else:
            while True:
                pwd = getpass.getpass("Yangi maxfiy parolni kiriting (kamida 8 belgi): ")
                valid, msg = validate_password(pwd)
                if not valid:
                    print(f"[XATO] {msg}")
                    continue
                pwd_confirm = getpass.getpass("Parolni tasdiqlash uchun qayta kiriting: ")
                if pwd != pwd_confirm:
                    print("[XATO] Kiritilgan parollar bir-biriga mos kelmadi! Qaytadan urinib ko'ring.\n")
                    continue
                break

        # Parolni scrypt yordamida xeshlash
        pwd_hash = generate_password_hash(pwd, method='scrypt')

        target_admin = Admin.query.filter_by(username=username).first()
        if target_admin:
            target_admin.full_name = full_name
            target_admin.phone = phone
            target_admin.password_hash = pwd_hash
            target_admin.is_active = True
            target_admin.is_password_changed = True
            target_admin.reset_failed_attempts()
            action_label = "yangilandi"
        else:
            target_admin = Admin(
                username=username,
                full_name=full_name,
                phone=phone,
                password_hash=pwd_hash,
                role='admin',
                is_active=True,
                is_password_changed=True
            )
            db.session.add(target_admin)
            action_label = "yaratildi"

        db.session.commit()

        print("\n" + "=" * 65)
        print(f"[MUVAFFAQIYATLI] Administrator '{username}' ({full_name}) {action_label}!")
        print("Tizimga kirish manzili: http://127.0.0.1:5000/login")
        print("=" * 65 + "\n")


if __name__ == '__main__':
    main()
