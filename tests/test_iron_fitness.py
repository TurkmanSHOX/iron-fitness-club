import os
import sys
import pytest
from datetime import date, datetime, timedelta

# Project root path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from app.config import Config
from app.extensions import db
from app.models.admin import Admin
from app.models.client import Client
from app.models.tariff import Tariff
from app.models.subscription import Subscription, FreezeRequest
from app.models.visit import Visit
from app.models.product import Product, ProductCategory, StockMovement
from app.models.sale import Sale
from app.models.payment import Payment
from app.models.expense import Expense
from app.services.subscription_service import calculate_subscription_end_date, create_subscription
from app.services.access_service import check_in_client
from app.services.freeze_service import create_freeze_request, approve_freeze_request, auto_unfreeze_expired_subscriptions
from app.services.pos_service import process_pos_checkout, refund_or_cancel_sale
from app.services.payment_service import ClickHandler, PaymeHandler
from app.services.pdf_service import generate_receipt_pdf, generate_qr_code_image
from app.services.excel_service import export_to_excel

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client_app(app):
    return app.test_client()

# =====================================================================
# 1. ADMIN VA AUTENTIFIKATSIYA TESTI
# =====================================================================
def test_admin_auth(app):
    with app.app_context():
        admin = Admin.query.filter_by(username='admin').first()
        assert admin is not None
        assert admin.check_password('admin123') is True
        assert admin.check_password('wrongpass') is False

# =====================================================================
# 2. TARIFLAR VA MIJOZ TESTI
# =====================================================================
def test_tariffs_and_client_creation(app):
    with app.app_context():
        # Dastlabki 4 ta tarif mavjudligini tekshirish
        tariffs = Tariff.query.all()
        assert len(tariffs) >= 4
        
        single_t = Tariff.query.filter_by(type='single').first()
        even_t = Tariff.query.filter_by(type='even_days').first()
        odd_t = Tariff.query.filter_by(type='odd_days').first()
        daily_t = Tariff.query.filter_by(type='daily').first()

        assert single_t.price == 20000
        assert even_t.price == 300000
        assert odd_t.price == 300000
        assert daily_t.price == 400000

        # Mijoz yaratish
        qr_token = Client.generate_unique_qr_code()
        assert qr_token.startswith("IFC-")
        
        c = Client(
            full_name="Testbek Karimov",
            phone="+998901112233",
            qr_code=qr_token,
            status="active"
        )
        db.session.add(c)
        db.session.commit()
        assert c.id is not None

# =====================================================================
# 3. ABONEMENT MUDDATI VA OY OXIRI QOIDASI
# =====================================================================
def test_subscription_date_calculation():
    # 31-yanvarda boshlangan 1 oylik abonement fevral oxirigacha amal qiladi
    jan_31 = date(2026, 1, 31)
    end_feb = calculate_subscription_end_date(jan_31, 30)
    assert end_feb == date(2026, 2, 28)

    # 15-martda boshlansa -> 15-aprel
    mar_15 = date(2026, 3, 15)
    end_apr = calculate_subscription_end_date(mar_15, 30)
    assert end_apr == date(2026, 4, 15)

    # 1 kunlik tashrif
    end_single = calculate_subscription_end_date(mar_15, 1)
    assert end_single == mar_15

# =====================================================================
# 4. JUFT / TOQ KUNLAR VA KIRISH NAZORATI TESTI
# =====================================================================
def test_access_control_and_scanner(app):
    with app.app_context():
        # Mijoz va juft kunlik tarif
        c = Client(
            full_name="Juftvoy Oripov",
            phone="+998912223344",
            qr_code="IFC-JUFT12345",
            status="active"
        )
        db.session.add(c)
        db.session.commit()

        even_tariff = Tariff.query.filter_by(type='even_days').first()
        today = date.today()

        # Bugundan boshlanuvchi abonement
        sub = create_subscription(
            client_id=c.id,
            tariff_id=even_tariff.id,
            payment_method='cash',
            start_date=today
        )
        assert sub.status == 'active'

        # Kirishni tekshirish
        result = check_in_client(c.qr_code, scan_type='qr')
        day_is_even = (today.day % 2 == 0)

        if day_is_even:
            assert result['success'] is True
            assert result['status'] == 'allowed'

            # Takroriy kirish sinovi: bir kunda 2-marta kirish bloklanishi kerak!
            dup_result = check_in_client(c.qr_code, scan_type='qr')
            assert dup_result['success'] is False
            assert "allaqachon kirgan" in dup_result['reason']

            # Admin istisno ruxsati bilan kiritish
            admin = Admin.query.first()
            override_res = check_in_client(c.qr_code, scan_type='manual', admin_id=admin.id, override_reason="Ruxsat berildi")
            assert override_res['success'] is True
        else:
            assert result['success'] is False
            assert "Juft kunlar" in result['reason']

# =====================================================================
# 5. ABONEMENTNI MUZLATISH VA MUDDAT UZAYTIRILISHI TESTI
# =====================================================================
def test_freeze_request_and_extension(app):
    with app.app_context():
        admin = Admin.query.first()
        daily_tariff = Tariff.query.filter_by(type='daily').first()

        c = Client(
            full_name="Muzlatbek Muzov",
            phone="+998933334455",
            qr_code="IFC-FREEZE1234",
            status="active"
        )
        db.session.add(c)
        db.session.commit()

        sub = create_subscription(
            client_id=c.id,
            tariff_id=daily_tariff.id,
            start_date=date.today()
        )
        original_end_date = sub.end_date

        # 5 kunga muzlatish so'rovi
        success, req = create_freeze_request(c.id, days_count=5, reason="Safarga ketayapman")
        assert success is True
        assert req.status == 'pending'

        # Admin tasdiqlashi
        app_res, msg = approve_freeze_request(req.id, admin_id=admin.id, admin_comment="Tasdiqlandi")
        assert app_res is True

        # Abonement holati 'frozen' bo'lishi va tugash sanasi 5 kunga uzaytirilishi kerak!
        sub_updated = db.session.get(Subscription, sub.id)
        assert sub_updated.status == 'frozen'
        assert sub_updated.end_date == original_end_date + timedelta(days=5)

        # Muzlatilgan paytda QR-kod orqali kirish bloklanishi kerak!
        check_res = check_in_client(c.qr_code)
        assert check_res['success'] is False
        assert "MUZLATILGAN" in check_res['reason']

# =====================================================================
# 6. POS KASSA VA OMBOR INTEGRATSIYASI TESTI
# =====================================================================
def test_pos_and_inventory_integration(app):
    with app.app_context():
        product = Product.query.filter_by(barcode='4780001234567').first() # Hydrolife suv
        assert product is not None
        initial_stock = product.stock_quantity

        # 3 dona suv sotish
        items = [{'product_id': product.id, 'quantity': 3}]
        success, sale = process_pos_checkout(items, payment_method='cash')
        assert success is True
        assert sale.final_amount == float(product.sale_price) * 3

        # Ombor qoldig'i 3 taga kamayishi kerak
        prod_after = db.session.get(Product, product.id)
        assert prod_after.stock_quantity == initial_stock - 3

        # Qaytarish (Refund) sinovi
        ref_success, ref_msg = refund_or_cancel_sale(sale.id, reason="Mijoz qaytardi")
        assert ref_success is True

        # Ombor qoldig'i qayta tiklanishi kerak
        prod_refunded = db.session.get(Product, product.id)
        assert prod_refunded.stock_quantity == initial_stock

# =====================================================================
# 7. CLICK VA PAYME WEBHOOK TESTLARI
# =====================================================================
def test_payment_webhooks(app):
    with app.app_context():
        c = Client(full_name="To'lovbek", phone="+998977778899", qr_code="IFC-PAYME123")
        db.session.add(c)
        db.session.commit()

        # Click Prepare & Complete
        click_data_prepare = {
            'click_trans_id': '1001',
            'service_id': '1',
            'merchant_trans_id': f'client_{c.id}_tariff_1',
            'amount': '20000',
            'action': 0,
            'error': 0,
            'sign_time': '2026-11-06 12:00:00',
            'sign_string': ''
        }
        res_prep = ClickHandler.handle_request(click_data_prepare)
        assert res_prep['error'] == 0

        click_data_complete = {
            'click_trans_id': '1001',
            'service_id': '1',
            'merchant_trans_id': f'client_{c.id}_tariff_1',
            'amount': '20000',
            'action': 1,
            'error': 0,
            'sign_time': '2026-11-06 12:00:00',
            'sign_string': ''
        }
        res_comp = ClickHandler.handle_request(click_data_complete)
        assert res_comp['error'] == 0
        assert c.active_subscription is not None

# =====================================================================
# 8. PDF VA EXCEL GENERATSIYA TESTI
# =====================================================================
def test_pdf_and_excel_generation(tmp_path):
    # QR rasmi
    qr_path = str(tmp_path / "test_qr.png")
    generate_qr_code_image("IFC-TEST123456", qr_path)
    assert os.path.exists(qr_path)

    # Elektron PDF chek
    receipt_data = {
        'receipt_number': 'CHK-TEST-001',
        'club_name': 'IRON FITNESS CLUB',
        'club_phone': '+998 90 123 45 67',
        'club_address': 'Urganch',
        'date_time': '06.11.2026 12:00',
        'client_name': 'Testbek',
        'items': [{'name': 'Hydrolife', 'qty': 1, 'price': 5000, 'total': 5000}],
        'subtotal': 5000,
        'discount': 0,
        'total': 5000,
        'payment_method': 'Naqd pul',
        'qr_token': 'CHK-TEST-001'
    }
    receipt_path = str(tmp_path / "test_receipt.pdf")
    generate_receipt_pdf(receipt_data, receipt_path)
    assert os.path.exists(receipt_path)
    assert os.path.getsize(receipt_path) > 0

    # Excel eksport
    excel_path = str(tmp_path / "test_report.xlsx")
    export_to_excel(
        title="Test Hisobot",
        headers=["ID", "Nomi", "Summa"],
        rows=[[1, "Tovar A", 10000], [2, "Tovar B", 25000]],
        output_path=excel_path
    )
    assert os.path.exists(excel_path)
    assert os.path.getsize(excel_path) > 0
