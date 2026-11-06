from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func
from app.extensions import db
from app.models.client import Client
from app.models.subscription import Subscription, FreezeRequest
from app.models.visit import Visit
from app.models.payment import Payment
from app.models.sale import Sale
from app.models.expense import Expense
from app.models.product import Product
from app.models.tariff import Tariff

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)

    # 1. Asosiy hisoblagichlar
    total_clients = Client.query.filter(Client.status != 'archived').count()
    active_subscriptions = Subscription.query.filter_by(status='active').count()
    expired_subscriptions = Subscription.query.filter_by(status='expired').count()
    frozen_subscriptions = Subscription.query.filter_by(status='frozen').count()
    today_visits = Visit.query.filter_by(visit_date=today, status='allowed').count()

    # 2. Bugungi moliyaviy ko'rsatkichlar
    today_sub_income = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        func.date(Payment.created_at) == today,
        Payment.status == 'completed',
        Payment.payment_type.in_(['subscription', 'single_visit'])
    ).scalar() or 0.0

    today_sale_income = db.session.query(func.coalesce(func.sum(Sale.final_amount), 0)).filter(
        func.date(Sale.created_at) == today,
        Sale.status == 'completed'
    ).scalar() or 0.0

    today_total_income = float(today_sub_income) + float(today_sale_income)

    today_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.expense_date == today
    ).scalar() or 0.0

    today_net_profit = today_total_income - float(today_expenses)

    # 3. Oylik moliyaviy ko'rsatkichlar
    month_sub_income = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        func.date(Payment.created_at) >= first_day_of_month,
        Payment.status == 'completed',
        Payment.payment_type.in_(['subscription', 'single_visit'])
    ).scalar() or 0.0

    month_sale_income = db.session.query(func.coalesce(func.sum(Sale.final_amount), 0)).filter(
        func.date(Sale.created_at) >= first_day_of_month,
        Sale.status == 'completed'
    ).scalar() or 0.0

    month_total_income = float(month_sub_income) + float(month_sale_income)

    month_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.expense_date >= first_day_of_month
    ).scalar() or 0.0

    month_net_profit = month_total_income - float(month_expenses)

    # 4. Ogohlantirishlar
    pending_freezes = FreezeRequest.query.filter_by(status='pending').count()
    low_stock_count = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.min_stock_alert
    ).count()

    expiring_soon_count = Subscription.query.filter(
        Subscription.status == 'active',
        Subscription.end_date >= today,
        Subscription.end_date <= (today + timedelta(days=3))
    ).count()

    # So'nggi 5 ta tashrif
    recent_visits = Visit.query.order_by(Visit.id.desc()).limit(5).all()

    # So'nggi 5 ta to'lov
    recent_payments = Payment.query.filter_by(status='completed').order_by(Payment.id.desc()).limit(5).all()

    return render_template(
        'dashboard/index.html',
        total_clients=total_clients,
        active_subscriptions=active_subscriptions,
        expired_subscriptions=expired_subscriptions,
        frozen_subscriptions=frozen_subscriptions,
        today_visits=today_visits,
        today_total_income=today_total_income,
        today_sub_income=today_sub_income,
        today_sale_income=today_sale_income,
        today_expenses=today_expenses,
        today_net_profit=today_net_profit,
        month_total_income=month_total_income,
        month_expenses=month_expenses,
        month_net_profit=month_net_profit,
        pending_freezes=pending_freezes,
        low_stock_count=low_stock_count,
        expiring_soon_count=expiring_soon_count,
        recent_visits=recent_visits,
        recent_payments=recent_payments
    )


@dashboard_bp.route('/api/charts')
@login_required
def charts_api():
    """Chart.js uchun real dinamik ma'lumotlar"""
    today = date.today()

    # 1. So'nggi 7 kunlik daromad va tashriflar
    days_labels = []
    revenue_data = []
    visits_data = []

    for i in range(6, -1, -1):
        target_day = today - timedelta(days=i)
        days_labels.append(target_day.strftime('%d-%b'))

        # Shu kungi tushum
        pay_sum = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
            func.date(Payment.created_at) == target_day,
            Payment.status == 'completed'
        ).scalar() or 0.0
        revenue_data.append(float(pay_sum))

        # Shu kungi tashriflar
        v_count = Visit.query.filter_by(visit_date=target_day, status='allowed').count()
        visits_data.append(v_count)

    # 2. Tariflar bo'yicha sotuv taqsimoti
    tariffs = Tariff.query.filter_by(is_active=True).all()
    tariff_labels = []
    tariff_counts = []
    for t in tariffs:
        cnt = Subscription.query.filter_by(tariff_id=t.id).count()
        tariff_labels.append(t.name)
        tariff_counts.append(cnt)

    return jsonify({
        'days_labels': days_labels,
        'revenue_data': revenue_data,
        'visits_data': visits_data,
        'tariff_labels': tariff_labels,
        'tariff_counts': tariff_counts
    })
