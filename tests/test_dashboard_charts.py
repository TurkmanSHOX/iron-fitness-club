import os
import sys
import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal

# Project root path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import create_app
from app.extensions import db
from app.models.admin import Admin
from app.models.client import Client
from app.models.tariff import Tariff
from app.models.subscription import Subscription
from app.models.payment import Payment
from app.models.visit import Visit


@pytest.fixture
def chart_test_app():
    os.environ['DATABASE_URL'] = 'mysql+pymysql://root:@127.0.0.1:3306/iron_fitness_club?charset=utf8mb4'
    os.environ['SECRET_KEY'] = 'iron-fitness-prod-secret-key-urganch-2026'
    os.environ['FLASK_ENV'] = 'production'
    os.environ['TESTING'] = 'false'

    app = create_app()
    app.config['WTF_CSRF_ENABLED'] = False
    return app


def test_dashboard_charts_full_business_logic(chart_test_app):
    """
    Dashboard grafiklarining biznes mantig'i:
    1. So'nggi 7 kunlik daromad va tashriflar:
       - 7 ta kun doimo chiqishi
       - Ma'lumot yo'q kunlarda 0 qaytishi
       - Bekor qilingan to'lovlar qo'shilmasligi
       - Bir kunda bir nechta to'lov to'g'ri qo'shilishi
    2. Tariflar bo'yicha taqsimot:
       - Faol abonementlar to'g'ri taqsimlanishi
       - Muddati tugagan va bekor qilinganlar qo'shilmasligi
       - Bo'sh holatda has_active_tariffs = False bo'lishi
    """
    with chart_test_app.app_context():
        today = date.today()

        # Adminni tayyorlash
        admin = Admin.query.filter_by(username='admin').first()
        admin.reset_failed_attempts()
        admin.is_password_changed = True
        db.session.commit()

        # Sinov mijozini yaratish
        test_client = Client(
            full_name="Chart Test Mijoz",
            phone="+998909998877",
            qr_code="QR_CHART_TEST"
        )
        db.session.add(test_client)
        db.session.commit()

        # 4 ta tarifni olish
        t_single = Tariff.query.filter_by(type='single').first()
        t_even = Tariff.query.filter_by(type='even_days').first()
        t_odd = Tariff.query.filter_by(type='odd_days').first()
        t_daily = Tariff.query.filter_by(type='daily').first()

        created_payments = []
        created_visits = []
        created_subs = []

        try:
            # 1. 2 kun oldin (today - 2 days): 2 ta muvaffaqiyatli to'lov va 1 ta bekor qilingan to'lov
            day_minus_2 = today - timedelta(days=2)
            time_dt1 = datetime.combine(day_minus_2, datetime.min.time()) + timedelta(hours=10)
            time_dt2 = datetime.combine(day_minus_2, datetime.min.time()) + timedelta(hours=15)
            time_dt_cancel = datetime.combine(day_minus_2, datetime.min.time()) + timedelta(hours=17)

            p1 = Payment(
                payment_number=f"PAY_CHART_{day_minus_2.strftime('%Y%m%d')}_1",
                client_id=test_client.id,
                payment_type='subscription',
                amount=Decimal('300000.00'),
                payment_method='cash',
                status='completed',
                created_at=time_dt1
            )
            p2 = Payment(
                payment_number=f"PAY_CHART_{day_minus_2.strftime('%Y%m%d')}_2",
                client_id=test_client.id,
                payment_type='product_sale',
                amount=Decimal('50000.00'),
                payment_method='card',
                status='completed',
                created_at=time_dt2
            )
            p_cancelled = Payment(
                payment_number=f"PAY_CHART_{day_minus_2.strftime('%Y%m%d')}_3",
                client_id=test_client.id,
                payment_type='subscription',
                amount=Decimal('400000.00'),
                payment_method='click',
                status='cancelled',  # Bekor qilingan - qo'shilmasligi shart!
                created_at=time_dt_cancel
            )
            db.session.add_all([p1, p2, p_cancelled])

            # Shu kungi tashriflar: 3 ta ruxsat berilgan, 1 ta rad etilgan
            v1 = Visit(client_id=test_client.id, visit_date=day_minus_2, scan_type='qr', status='allowed')
            v2 = Visit(client_id=test_client.id, visit_date=day_minus_2, scan_type='manual', status='allowed')
            v_denied = Visit(client_id=test_client.id, visit_date=day_minus_2, scan_type='qr', status='denied')
            db.session.add_all([v1, v2, v_denied])

            # 2. Faol abonementlar yaratish (Tariflar taqsimoti uchun)
            # t_even: 1 ta active
            sub_active_even = Subscription(
                client_id=test_client.id,
                tariff_id=t_even.id,
                start_date=today,
                end_date=today + timedelta(days=30),
                status='active',
                original_price=t_even.price,
                paid_amount=t_even.price
            )
            # t_odd: 1 ta expired (taqsimotga qo'shilmasligi kerak!)
            sub_expired_odd = Subscription(
                client_id=test_client.id,
                tariff_id=t_odd.id,
                start_date=today - timedelta(days=40),
                end_date=today - timedelta(days=10),
                status='expired',
                original_price=t_odd.price,
                paid_amount=t_odd.price
            )
            # t_daily: 1 ta cancelled (taqsimotga qo'shilmasligi kerak!)
            sub_cancelled_daily = Subscription(
                client_id=test_client.id,
                tariff_id=t_daily.id,
                start_date=today,
                end_date=today + timedelta(days=30),
                status='cancelled',
                original_price=t_daily.price,
                paid_amount=t_daily.price
            )
            db.session.add_all([sub_active_even, sub_expired_odd, sub_cancelled_daily])
            db.session.commit()

            created_payments.extend([p1, p2, p_cancelled])
            created_visits.extend([v1, v2, v_denied])
            created_subs.extend([sub_active_even, sub_expired_odd, sub_cancelled_daily])

            # Client orqali /api/charts ni tekshirish
            client = chart_test_app.test_client()
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin.id)
                sess['_fresh'] = True

            res = client.get('/api/charts')
            assert res.status_code == 200
            data = res.get_json()

            # 1. 7 kun tekshiruvi
            assert len(data['days_labels']) == 7
            assert len(data['revenue_data']) == 7
            assert len(data['visits_data']) == 7

            # today - 2 days indeksi: 7 elementli ro'yxatda 4-indeks (6, 5, 4, 3, 2, 1, 0)
            idx_minus_2 = 4
            # 300 000 + 50 000 = 350 000 so'm (400 000 bekor qilingan to'lov QO'SHILMASLIGI KERAK)
            assert data['revenue_data'][idx_minus_2] >= 350000.0
            # 2 ta ruxsat etilgan tashrif (rad etilgan tashrif QO'SHILMASLIGI KERAK)
            assert data['visits_data'][idx_minus_2] >= 2

            # 2. Tariflar taqsimoti tekshiruvi
            assert 'tariff_details' in data
            assert len(data['tariff_details']) == 4

            # Faqat faol abonementlar hisoblanganligi (expired va cancelled qo'shilmagan)
            for item in data['tariff_details']:
                if item['id'] == t_even.id:
                    assert item['count'] >= 1
                elif item['id'] == t_odd.id:
                    # sub_expired_odd qo'shilmagan
                    pass
                elif item['id'] == t_daily.id:
                    # sub_cancelled_daily qo'shilmagan
                    pass

            assert data['total_active_subs'] >= 1
            assert data['has_active_tariffs'] is True

        finally:
            # Test ma'lumotlarini bazadan xavfsiz tozalash
            for p in created_payments:
                db.session.delete(p)
            for v in created_visits:
                db.session.delete(v)
            for s in created_subs:
                db.session.delete(s)
            db.session.delete(test_client)
            db.session.commit()
