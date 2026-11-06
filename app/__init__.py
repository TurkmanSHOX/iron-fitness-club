import os
from flask import Flask, render_template
from app.config import Config
from app.extensions import db, login_manager, scheduler
from app.models.admin import Admin
from app.models.setting import Setting
from app.models.tariff import Tariff
from app.models.product import ProductCategory, Product, Supplier
from app.models.subscription import FreezeRequest
from app.services.scheduler_service import start_scheduler

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Kataloglarni mavjudligini ta'minlash
    for d in [Config.UPLOAD_FOLDER, Config.REPORTS_FOLDER, Config.RECEIPTS_FOLDER, Config.QRCODES_FOLDER, Config.BACKUPS_FOLDER]:
        os.makedirs(d, exist_ok=True)

    # Kengaytmalarni ulash
    db.init_app(app)
    login_manager.init_app(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        return Admin.query.get(int(user_id))

    # Blueprintlarni ro'yxatdan o'tkazish
    from app.routes.auth_routes import auth_bp
    from app.routes.dashboard_routes import dashboard_bp
    from app.routes.client_routes import client_bp
    from app.routes.tariff_routes import tariff_bp
    from app.routes.subscription_routes import subscription_bp
    from app.routes.visit_routes import visit_bp
    from app.routes.pos_routes import pos_bp
    from app.routes.inventory_routes import inventory_bp
    from app.routes.expense_routes import expense_bp
    from app.routes.promotion_routes import promotion_bp
    from app.routes.report_routes import report_bp
    from app.routes.setting_routes import setting_bp
    from app.routes.api_routes import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(client_bp, url_prefix='/clients')
    app.register_blueprint(tariff_bp, url_prefix='/tariffs')
    app.register_blueprint(subscription_bp, url_prefix='/subscriptions')
    app.register_blueprint(visit_bp, url_prefix='/visits')
    app.register_blueprint(pos_bp, url_prefix='/pos')
    app.register_blueprint(inventory_bp, url_prefix='/inventory')
    app.register_blueprint(expense_bp, url_prefix='/expenses')
    app.register_blueprint(promotion_bp, url_prefix='/promotions')
    app.register_blueprint(report_bp, url_prefix='/reports')
    app.register_blueprint(setting_bp, url_prefix='/settings')
    app.register_blueprint(api_bp)

    # Umumiy shablon o'zgaruvchilari (Sidebar va Navbar uchun)
    @app.context_processor
    def inject_global_vars():
        try:
            club_name = Setting.get_value('club_name', 'IRON FITNESS CLUB')
            pending_count = FreezeRequest.query.filter_by(status='pending').count()
            low_stock_count = Product.query.filter(
                Product.is_active == True,
                Product.stock_quantity <= Product.min_stock_alert
            ).count()
        except Exception:
            club_name = 'IRON FITNESS CLUB'
            pending_count = 0
            low_stock_count = 0

        return {
            'club_title': club_name,
            'global_pending_freezes': pending_count,
            'global_low_stock_count': low_stock_count
        }

    # Xatolik sahifalari
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    # Baza jadvallarini tekshirish va dastlabki ma'lumotlarni kiritish (Auto-seed)
    with app.app_context():
        try:
            db.create_all()
            _init_seed_data()
        except Exception as e:
            app.logger.warning(f"Baza initsializatsiyasida ogohlantirish: {e}")

        # Scheduler ishga tushirish (faqat asosiy jarayonda va test bo'lmaganda)
        if not app.config.get('TESTING') and (not app.debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true'):
            try:
                start_scheduler(app)
            except Exception as e:
                app.logger.warning(f"Scheduler ishga tushmadi: {e}")

    return app


def _init_seed_data():
    """Baza bo'sh bo'lsa, dastlabki admin, tariflar va sozlamalarni yaratadi"""
    # 1. Admin
    admin = Admin.query.first()
    if not admin:
        default_admin = Admin(
            username='admin',
            full_name='Bosh Administrator',
            phone='+998901234567',
            role='admin',
            is_active=True
        )
        default_admin.set_password('admin123')
        db.session.add(default_admin)

    # 2. Dastlabki 4 ta tarif
    if Tariff.query.count() == 0:
        tariffs = [
            Tariff(name='1 kunlik tashrif', type='single', duration_days=1, price=20000, description="Zalga 1 martalik bir kunlik kirish", is_active=True),
            Tariff(name='1 oylik - Juft kunlar', type='even_days', duration_days=30, price=300000, description="Faqat oyning juft sanalarida (2, 4, 6, 8, 10...) kirish", is_active=True),
            Tariff(name='1 oylik - Toq kunlar', type='odd_days', duration_days=30, price=300000, description="Faqat oyning toq sanalarida (1, 3, 5, 7, 9...) kirish", is_active=True),
            Tariff(name='1 oylik - Har kuni', type='daily', duration_days=30, price=400000, description="Oyning barcha kunlarida cheklovsiz kirish", is_active=True),
        ]
        db.session.add_all(tariffs)

    # 3. Sozlamalar
    defaults = {
        'club_name': 'IRON FITNESS CLUB',
        'club_phone': '+998 90 123 45 67',
        'club_address': 'Urganch shahri, Al-Xorazmiy ko\'chasi, 24-uy',
        'currency': 'UZS',
        'max_freeze_days': '10',
        'max_freeze_per_period': '1',
        'single_entry_per_day': 'true'
    }
    for k, v in defaults.items():
        if not Setting.query.filter_by(setting_key=k).first():
            db.session.add(Setting(setting_key=k, setting_value=v))

    # 4. Mahsulot kategoriyalari va tovarlar
    if ProductCategory.query.count() == 0:
        cat1 = ProductCategory(name='Suv va Ichimliklar', description='Mineral va sport ichimliklari')
        cat2 = ProductCategory(name='Energetiklar', description='Energetik ichimliklar')
        cat3 = ProductCategory(name='Sport oziq-ovqatlari', description='Protein, kreatin')
        cat4 = ProductCategory(name='Protein batonchalari', description='Sport batonchalari')
        db.session.add_all([cat1, cat2, cat3, cat4])
        db.session.flush()

        sup = Supplier(name='Sport Nutrition Tashkent', phone='+998712001122', address='Toshkent')
        db.session.add(sup)
        db.session.flush()

        prods = [
            Product(name='Hydrolife Gazsiz Suv 0.5L', barcode='4780001234567', category_id=cat1.id, supplier_id=sup.id, purchase_price=2500, sale_price=5000, stock_quantity=50, unit='dona', min_stock_alert=10),
            Product(name='Flash Up Max 0.45L', barcode='4600682012345', category_id=cat2.id, supplier_id=sup.id, purchase_price=7000, sale_price=12000, stock_quantity=30, unit='dona', min_stock_alert=8),
            Product(name='Gold Standard Whey 100% 908g', barcode='6901234567890', category_id=cat3.id, supplier_id=sup.id, purchase_price=280000, sale_price=390000, stock_quantity=10, unit='banka', min_stock_alert=3),
            Product(name='Bombbar Protein Batoncha 60g', barcode='4620012345678', category_id=cat4.id, supplier_id=sup.id, purchase_price=12000, sale_price=20000, stock_quantity=40, unit='dona', min_stock_alert=10),
            Product(name='Creatine Monohydrate 300g', barcode='7901234567891', category_id=cat3.id, supplier_id=sup.id, purchase_price=130000, sale_price=190000, stock_quantity=15, unit='banka', min_stock_alert=4)
        ]
        db.session.add_all(prods)

    db.session.commit()
