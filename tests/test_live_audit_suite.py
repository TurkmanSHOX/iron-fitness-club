import os
import sys
import re
import gzip
import shutil
import secrets
import base64
import hashlib
import pytest
import pymysql
from datetime import datetime, date, timedelta
from decimal import Decimal

# Project root path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Set environment before loading app
os.environ['DATABASE_URL'] = 'mysql+pymysql://root:@127.0.0.1:3306/iron_fitness_club?charset=utf8mb4'
os.environ['SECRET_KEY'] = 'iron-fitness-prod-secret-key-urganch-2026'
os.environ['FLASK_ENV'] = 'production'
os.environ['TESTING'] = 'false'

from app import create_app
from app.config import Config
from app.extensions import db
from app.models.admin import Admin
from app.models.client import Client, ClientQRCode
from app.models.tariff import Tariff
from app.models.subscription import Subscription, FreezeRequest
from app.models.visit import Visit, AccessAttempt
from app.models.product import Product, ProductCategory, StockMovement
from app.models.sale import Sale
from app.models.expense import Expense
from app.models.setting import Setting, AuditLog, BackupLog
from app.services.access_service import check_in_client
from app.services.payment_service import ClickHandler, PaymeHandler
from scripts.backup import make_backup, restore_backup, parse_database_url


def extract_csrf_token(html_text):
    """HTML sahifasidan CSRF tokenini xavfsiz ajratib olish"""
    m = re.search(r'name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']', html_text)
    if not m:
        m = re.search(r'value=["\']([^"\']+)["\'][^>]*name=["\']csrf_token["\']', html_text)
    return m.group(1) if m else ''


class TestLiveRealEnvironment:
    """
    IRON FITNESS CLUB — Haqiqiy MariaDB va ishlab chiqarish muhitida to'liq amaliy sinov
    """

    @pytest.fixture(autouse=True)
    def setup_app(self):
        self.app = create_app()
        self.client = self.app.test_client()
        with self.app.app_context():
            # Admin hisobini faol va parol almashtirilgan holatga keltirish
            admin = Admin.query.filter_by(username='admin').first()
            if admin:
                admin.reset_failed_attempts()
                admin.is_password_changed = True
                db.session.commit()
            yield

    def login_admin(self):
        # 1. Login sahifasidan CSRF tokenni olish
        resp = self.client.get('/login')
        token = extract_csrf_token(resp.data.decode('utf-8'))
        return self.client.post('/login', data={
            'username': 'admin',
            'password': 'admin123',
            'csrf_token': token
        }, follow_redirects=True)

    # =========================================================================
    # 1. MARIADB MA'LUMOTLAR BAZASI TEKSHIRUVI
    # =========================================================================
    def test_01_mariadb_tables_innodb_and_utf8mb4(self):
        """Barcha 25 ta jadval MariaDB, InnoDB va utf8mb4_unicode_ci ekanligini tekshirish"""
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='', db='iron_fitness_club')
        cur = conn.cursor()
        cur.execute("""
            SELECT TABLE_NAME, ENGINE, TABLE_COLLATION 
            FROM information_schema.TABLES 
            WHERE TABLE_SCHEMA = 'iron_fitness_club'
        """)
        tables = cur.fetchall()
        conn.close()

        assert len(tables) == 25, f"Kutilgan 25 ta jadval, lekin {len(tables)} ta topildi"
        for name, engine, collation in tables:
            assert engine == 'InnoDB', f"Jadval {name} InnoDB emas: {engine}"
            assert 'utf8mb4' in collation, f"Jadval {name} utf8mb4 emas: {collation}"

    def test_02_mariadb_live_crud_and_persistence(self):
        """MariaDB da real CRUD va ma'lumotlar saqlanishini tekshirish"""
        with self.app.app_context():
            test_phone = f"+99890{datetime.now().strftime('%H%M%S%f')[:7]}"
            new_client = Client(
                full_name="Haqiqiy Sinovchi",
                phone=test_phone,
                qr_code=f"QR_{datetime.now().strftime('%H%M%S%f')[:8]}"
            )
            db.session.add(new_client)
            db.session.commit()
            client_id = new_client.id

            # Boshqa so'rov orqali qayta o'qish
            loaded = db.session.get(Client, client_id)
            assert loaded is not None
            assert loaded.full_name == "Haqiqiy Sinovchi"
            assert loaded.phone == test_phone

            # Update
            loaded.full_name = "Haqiqiy Yangilangan"
            db.session.commit()
            updated = db.session.get(Client, client_id)
            assert updated.full_name == "Haqiqiy Yangilangan"

            # Delete
            db.session.delete(updated)
            db.session.commit()
            assert db.session.get(Client, client_id) is None

    # =========================================================================
    # 2. FLASK BARCHA SAHIFALARI (11 TA BO'LIM) SMOKE TEST
    # =========================================================================
    def test_03_flask_all_11_views_smoke_test(self):
        """11 ta asosiy bo'lim sahifalari HTTP 200 qaytarishini tekshirish"""
        login_res = self.login_admin()
        assert login_res.status_code == 200

        routes = [
            ('/', 'Boshqaruv paneli'),
            ('/clients/', 'Mijozlar ro\'yxati'),
            ('/tariffs/', 'Tariflar'),
            ('/visits/scanner', 'QR Skaner oynasi'),
            ('/visits/history', 'Tashriflar tarixi'),
            ('/pos/', 'Savdo va kassa'),
            ('/pos/sales', 'Savdolar tarixi'),
            ('/inventory/', 'Ombor'),
            ('/subscriptions/', 'Abonementlar'),
            ('/expenses/', 'Xarajatlar'),
            ('/reports/', 'Hisobotlar'),
            ('/settings/', 'Sozlamalar')
        ]

        for url, name in routes:
            resp = self.client.get(url, follow_redirects=True)
            assert resp.status_code == 200, f"Sahifa ochilmadi: {name} ({url}) status={resp.status_code}"

    def test_04_flask_crud_via_routes(self):
        """Web marshrutlar orqali CSRF bilan yangi mijoz va yangi xarajat qo'shish"""
        self.login_admin()

        # 1. Mijoz qo'shish formasi va CSRF
        add_client_get = self.client.get('/clients/add')
        assert add_client_get.status_code == 200
        client_csrf = extract_csrf_token(add_client_get.data.decode('utf-8'))

        unique_phone = f"+99899{datetime.now().strftime('%H%M%S%f')[:7]}"
        add_client_resp = self.client.post('/clients/add', data={
            'csrf_token': client_csrf,
            'full_name': 'Web Sinov Mijoz',
            'phone': unique_phone,
            'birth_date': '1995-05-15',
            'gender': 'male',
            'notes': 'Web form test'
        }, follow_redirects=True)
        assert add_client_resp.status_code == 200

        with self.app.app_context():
            created_client = Client.query.filter_by(phone=unique_phone).first()
            assert created_client is not None
            assert created_client.qr_code is not None

        # 2. Yangi xarajat qo'shish formasi va CSRF
        add_exp_get = self.client.get('/expenses/add')
        assert add_exp_get.status_code == 200
        exp_csrf = extract_csrf_token(add_exp_get.data.decode('utf-8'))

        exp_title = f"Test Kommunal {datetime.now().strftime('%H%M%S')}"
        exp_resp = self.client.post('/expenses/add', data={
            'csrf_token': exp_csrf,
            'title': exp_title,
            'amount': '150000',
            'category': 'electricity',
            'payment_method': 'cash',
            'expense_date': date.today().strftime('%Y-%m-%d'),
            'notes': 'Amaliy test xarajati'
        }, follow_redirects=True)
        assert exp_resp.status_code == 200

        with self.app.app_context():
            exp = Expense.query.filter_by(title=exp_title).first()
            assert exp is not None
            assert exp.amount == Decimal('150000.00')

    # =========================================================================
    # 3. QR-SKANER SINOVI (8 TA AMALIY HOLAT)
    # =========================================================================
    def test_05_qr_scanner_all_8_scenarios(self):
        """
        QR-skaner 8 xil amaliy holat:
        1. Faol abonement -> ruxsat
        2. Muddati tugagan abonement -> rad etish
        3. To'lov qilmagan mijoz -> rad etish
        4. Muzlatilgan abonement -> rad etish
        5. Juft kunlar tarifi toq kunda -> rad etish
        6. Toq kunlar tarifi juft kunda -> rad etish
        7. Bir kunda 2-marta kirish -> rad etish
        8. Qo'lda ruxsat berish (override) -> sabab bilan ruxsat va audit log
        """
        with self.app.app_context():
            t_daily = Tariff.query.filter_by(type='daily').first()
            t_even = Tariff.query.filter_by(type='even_days').first()
            t_odd = Tariff.query.filter_by(type='odd_days').first()

            assert t_daily is not None
            assert t_even is not None
            assert t_odd is not None

            # 1-holat: Faol abonementga ega mijoz
            u_suffix = secrets.token_hex(3)
            c1 = Client(full_name="Faol Mijoz", phone=f"+99891{u_suffix}1", qr_code=f"QR1_{u_suffix}")
            db.session.add(c1)
            db.session.commit()
            sub1 = Subscription(client_id=c1.id, tariff_id=t_daily.id, start_date=date.today() - timedelta(days=5), end_date=date.today() + timedelta(days=25), status='active', original_price=t_daily.price, paid_amount=t_daily.price)
            db.session.add(sub1)
            db.session.commit()

            res1 = check_in_client(c1.qr_code)
            assert res1['success'] is True
            assert res1['status'] == 'allowed'

            # 7-holat: Bir kunda 2-marta kirish (aynan shu c1 mijoz qayta kirmoqda)
            res7 = check_in_client(c1.qr_code)
            assert res7['success'] is False
            assert 'allaqachon kirgan' in res7['reason'].lower() or res7['status'] == 'denied'

            # 2-holat: Muddati tugagan abonement
            c2 = Client(full_name="Muddati O'tgan", phone=f"+99891{u_suffix}2", qr_code=f"QR2_{u_suffix}")
            db.session.add(c2)
            db.session.commit()
            sub2 = Subscription(client_id=c2.id, tariff_id=t_daily.id, start_date=date.today() - timedelta(days=40), end_date=date.today() - timedelta(days=10), status='active', original_price=t_daily.price, paid_amount=t_daily.price)
            db.session.add(sub2)
            db.session.commit()

            res2 = check_in_client(c2.qr_code)
            assert res2['success'] is False
            assert res2['status'] == 'denied'
            assert 'tugagan' in res2['reason'].lower()

            # 3-holat: To'lov qilmagan / abonementsiz mijoz
            c3 = Client(full_name="To'lovsiz Mijoz", phone=f"+99891{u_suffix}3", qr_code=f"QR3_{u_suffix}")
            db.session.add(c3)
            db.session.commit()
            res3 = check_in_client(c3.qr_code)
            assert res3['success'] is False
            assert res3['status'] == 'denied'
            assert 'abonement mavjud emas' in res3['reason'].lower()

            # 4-holat: Muzlatilgan abonement
            c4 = Client(full_name="Muzlatilgan Mijoz", phone=f"+99891{u_suffix}4", qr_code=f"QR4_{u_suffix}")
            db.session.add(c4)
            db.session.commit()
            sub4 = Subscription(client_id=c4.id, tariff_id=t_daily.id, start_date=date.today() - timedelta(days=5), end_date=date.today() + timedelta(days=25), status='frozen', original_price=t_daily.price, paid_amount=t_daily.price)
            db.session.add(sub4)
            db.session.commit()
            res4 = check_in_client(c4.qr_code)
            assert res4['success'] is False
            assert res4['status'] == 'denied'
            assert 'muzlatilgan' in res4['reason'].lower()

            # 5 & 6-holat: Kun turi mos kelmasligi (Juft / Toq)
            today_day = date.today().day
            is_today_even = (today_day % 2 == 0)

            c_opposite = Client(full_name="KunMosEmas Mijoz", phone=f"+99891{u_suffix}5", qr_code=f"QR5_{u_suffix}")
            db.session.add(c_opposite)
            db.session.commit()

            opposite_tariff = t_odd if is_today_even else t_even
            sub_opposite = Subscription(client_id=c_opposite.id, tariff_id=opposite_tariff.id, start_date=date.today() - timedelta(days=1), end_date=date.today() + timedelta(days=29), status='active', original_price=opposite_tariff.price, paid_amount=opposite_tariff.price)
            db.session.add(sub_opposite)
            db.session.commit()

            res_mismatch = check_in_client(c_opposite.qr_code)
            assert res_mismatch['success'] is False
            assert res_mismatch['status'] == 'denied'
            assert ('juft' in res_mismatch['reason'].lower() or 'toq' in res_mismatch['reason'].lower())

            # 8-holat: Administrator tomonidan qo'lda ruxsat berish (Manual Override)
            c8 = Client(full_name="Qo'lda Ruxsat", phone=f"+99891{u_suffix}8", qr_code=f"QR8_{u_suffix}")
            db.session.add(c8)
            db.session.commit()

            admin = Admin.query.first()
            override_res = check_in_client(
                c8.qr_code,
                scan_type='manual',
                admin_id=admin.id,
                override_reason="Mijoz kartasini unutib qoldirgan, shaxsi tasdiqlandi"
            )
            assert override_res['success'] is True
            assert override_res['status'] == 'allowed'

            # Audit log tekshiruvi
            last_audit = AuditLog.query.filter_by(action='ACCESS_OVERRIDE').order_by(AuditLog.id.desc()).first()
            assert last_audit is not None
            assert str(c8.id) in str(last_audit.target_id) or c8.full_name in last_audit.details

    # =========================================================================
    # 4. CLICK VA PAYME TO'LOVLARI (TEST VA PROTOKOL SINOVI)
    # =========================================================================
    def test_06_click_and_payme_full_cycle(self):
        """Click va Payme to'lovlarining test muhitidagi to'liq protokoli va obuna faollashuvi"""
        orig_click_key = Config.CLICK_SECRET_KEY
        orig_payme_key = Config.PAYME_SECRET_KEY

        try:
            # Test kalitlarini o'rnatish
            test_click_secret = "test_click_secret_key_12345"
            test_payme_secret = "test_payme_secret_key_12345"
            Config.CLICK_SECRET_KEY = test_click_secret
            Config.PAYME_SECRET_KEY = test_payme_secret

            with self.app.app_context():
                tariff = Tariff.query.filter_by(type='daily').first()
                c = Client(full_name="Payment Test Client", phone=f"+99890{datetime.now().strftime('%H%M%S%f')[:7]}", qr_code=f"QR_PAY_{datetime.now().strftime('%H%M%S%f')[:6]}")
                db.session.add(c)
                db.session.commit()

                # CLICK SINOVI
                order_id = f"client_{c.id}_tariff_{tariff.id}"
                click_trans_id = '9901'
                service_id = '1'
                amount_str = str(int(tariff.price))
                sign_time = '2026-11-06 12:00:00'

                # Click MD5 imzosini hisoblash
                to_hash_prep = f"{click_trans_id}{service_id}{test_click_secret}{order_id}{amount_str}0{sign_time}"
                sign_string_prep = hashlib.md5(to_hash_prep.encode('utf-8')).hexdigest()

                prep_payload = {
                    'click_trans_id': click_trans_id,
                    'service_id': service_id,
                    'merchant_trans_id': order_id,
                    'amount': amount_str,
                    'action': 0,
                    'error': 0,
                    'sign_time': sign_time,
                    'sign_string': sign_string_prep
                }
                res_prep = ClickHandler.handle_request(prep_payload)
                assert res_prep['error'] == 0
                prep_id = res_prep['merchant_prepare_id']

                # Click Complete
                to_hash_comp = f"{click_trans_id}{service_id}{test_click_secret}{order_id}{amount_str}1{sign_time}"
                sign_string_comp = hashlib.md5(to_hash_comp.encode('utf-8')).hexdigest()

                comp_payload = {
                    'click_trans_id': click_trans_id,
                    'service_id': service_id,
                    'merchant_trans_id': order_id,
                    'merchant_prepare_id': prep_id,
                    'amount': amount_str,
                    'action': 1,
                    'error': 0,
                    'sign_time': sign_time,
                    'sign_string': sign_string_comp
                }
                res_comp = ClickHandler.handle_request(comp_payload)
                assert res_comp['error'] == 0

                # Idempotency: Takroriy Complete yangi obuna yaratmaydi
                res_comp_repeat = ClickHandler.handle_request(comp_payload)
                assert res_comp_repeat['error'] == 0
                assert res_comp_repeat['error_note'] == 'Already completed'

                # PAYME SINOVI
                auth_str = base64.b64encode(f"Paycom:{test_payme_secret}".encode('utf-8')).decode('utf-8')
                auth_header = f"Basic {auth_str}"

                amount_tiyin = int(tariff.price * 100)
                payme_tx_id = f"payme_live_{datetime.now().strftime('%H%M%S%f')}"

                # 1. CheckPerformTransaction
                chk = PaymeHandler.handle_rpc(auth_header, {
                    "method": "CheckPerformTransaction",
                    "params": {"amount": amount_tiyin, "account": {"client_id": c.id, "tariff_id": tariff.id}},
                    "id": 10
                })
                assert chk.get('result', {}).get('allow') is True

                # 2. PerformTransaction
                perf = PaymeHandler.handle_rpc(auth_header, {
                    "method": "PerformTransaction",
                    "params": {"id": payme_tx_id, "amount": amount_tiyin, "account": {"client_id": c.id, "tariff_id": tariff.id}},
                    "id": 11
                })
                assert perf.get('result', {}).get('state') == 2

                # 3. CheckTransaction
                chk_tx = PaymeHandler.handle_rpc(auth_header, {
                    "method": "CheckTransaction",
                    "params": {"id": payme_tx_id},
                    "id": 12
                })
                assert chk_tx.get('result', {}).get('state') == 2

                # 4. CancelTransaction
                can = PaymeHandler.handle_rpc(auth_header, {
                    "method": "CancelTransaction",
                    "params": {"id": payme_tx_id, "reason": 1},
                    "id": 13
                })
                assert can.get('result', {}).get('state') == -2

        finally:
            Config.CLICK_SECRET_KEY = orig_click_key
            Config.PAYME_SECRET_KEY = orig_payme_key

    # =========================================================================
    # 5. ZAXIRA VA TIKLASH (BACKUP & RESTORE) HAQIQIY MARIADB DA SINOVI
    # =========================================================================
    def test_07_backup_and_restore_cycle(self):
        """
        MariaDB zaxira nusxasi olish (.sql.gz), alohida test bazani (iron_fitness_test_restore)
        yaratish, unga tiklash, jadvallarni solishtirish va tozalash.
        """
        # 1. Zaxira olish
        success, backup_path = make_backup(backup_type='manual', compress=True)
        assert success is True
        assert os.path.exists(backup_path)
        assert backup_path.endswith('.sql.gz')
        assert os.path.getsize(backup_path) > 0

        # 2. Alohida test bazani yaratish
        conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='')
        cur = conn.cursor()
        test_restore_db = 'iron_fitness_test_restore'
        cur.execute(f"DROP DATABASE IF EXISTS `{test_restore_db}`")
        cur.execute(f"CREATE DATABASE `{test_restore_db}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()

        # 3. Tiklashni amalga oshirish
        ok, msg = restore_backup(backup_path, target_db=test_restore_db)
        assert ok is True, f"Tiklash muvaffaqiyatsiz: {msg}"

        # 4. Asl baza va tiklangan bazadagi jadvallarni solishtirish
        cur.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'iron_fitness_club'")
        orig_tables = set(r[0] for r in cur.fetchall())

        cur.execute(f"SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{test_restore_db}'")
        restored_tables = set(r[0] for r in cur.fetchall())

        assert orig_tables == restored_tables, "Tiklangan bazada jadvallar asl nusxa bilan bir xil emas!"

        # Adminlar soni solishtirish
        cur.execute("SELECT COUNT(*) FROM iron_fitness_club.admins")
        orig_count = cur.fetchone()[0]

        cur.execute(f"SELECT COUNT(*) FROM {test_restore_db}.admins")
        restored_count = cur.fetchone()[0]
        assert orig_count == restored_count

        # 5. Sinov bazasini xavfsiz tozalash
        cur.execute(f"DROP DATABASE `{test_restore_db}`")
        conn.commit()
        conn.close()

    # =========================================================================
    # 6. XAVFSIZLIK VA AUDIT LOG TEKSHIRUVI
    # =========================================================================
    def test_08_security_and_audit_checks(self):
        """Parol xeshlash (scrypt), CSRF himoyasi va audit jurnali yozilishi"""
        with self.app.app_context():
            admin = Admin.query.first()
            assert admin.password_hash.startswith('scrypt:'), "Parol scrypt yordamida xeshlangan bo'lishi shart"

            # AuditLog yozilishi
            test_audit = AuditLog.log(
                action='TEST_AUDIT_ACTION',
                admin_id=admin.id,
                details="Xavfsizlik audit sinovi"
            )
            assert test_audit.id is not None
            found_audit = AuditLog.query.filter_by(action='TEST_AUDIT_ACTION').first()
            assert found_audit is not None

            # 5 ta xato urinishda bloklash funksiyasi
            admin.failed_login_attempts = 4
            db.session.commit()
            admin.increment_failed_attempts(max_attempts=5, lock_minutes=15)
            assert admin.is_locked is True
            assert admin.locked_until is not None

            # Qayta tiklash
            admin.reset_failed_attempts()
            db.session.commit()
            assert admin.is_locked is False

    # =========================================================================
    # 7. TELEGRAM BOT TOKEN HOLATI VA HANDLER MANTIG'I SINOVI
    # =========================================================================
    def test_09_telegram_bot_token_status(self):
        """Telegram bot tokeni .env da mavjud emasligini ochiq aniqlash"""
        token = os.environ.get('TELEGRAM_BOT_TOKEN', '').strip()
        # Haqiqiy token sozlanmagan bo'lsa, 'TASHQI MA'LUMOT TALAB QILINADI' sifatida qayd etiladi
        assert token == '', "Telegram bot tokeni bo'sh bo'lishi kutilgan (real token taqdim etilmagan)"
