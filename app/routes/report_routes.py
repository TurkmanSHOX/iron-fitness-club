import os
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from flask_login import login_required
from sqlalchemy import func
from app.extensions import db
from app.config import Config
from app.models.payment import Payment
from app.models.sale import Sale
from app.models.expense import Expense
from app.models.visit import Visit
from app.models.client import Client
from app.models.subscription import Subscription
from app.models.product import Product
from app.services.excel_service import export_to_excel

report_bp = Blueprint('reports', __name__)

@report_bp.route('/')
@login_required
def index():
    report_type = request.args.get('type', 'finance')
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')

    today = date.today()
    if not start_date_str:
        start_date = date(today.year, today.month, 1)
    else:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        except Exception:
            start_date = date(today.year, today.month, 1)

    if not end_date_str:
        end_date = today
    else:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except Exception:
            end_date = today

    # 1. Moliyaviy hisobot
    total_sub_income = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        func.date(Payment.created_at) >= start_date,
        func.date(Payment.created_at) <= end_date,
        Payment.status == 'completed',
        Payment.payment_type.in_(['subscription', 'single_visit'])
    ).scalar() or 0.0

    total_bar_income = db.session.query(func.coalesce(func.sum(Sale.final_amount), 0)).filter(
        func.date(Sale.created_at) >= start_date,
        func.date(Sale.created_at) <= end_date,
        Sale.status == 'completed'
    ).scalar() or 0.0

    total_expenses = db.session.query(func.coalesce(func.sum(Expense.amount), 0)).filter(
        Expense.expense_date >= start_date,
        Expense.expense_date <= end_date
    ).scalar() or 0.0

    total_income = float(total_sub_income) + float(total_bar_income)
    net_profit = total_income - float(total_expenses)

    # To'lov turlari kesimida
    cash_payments = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        func.date(Payment.created_at) >= start_date,
        func.date(Payment.created_at) <= end_date,
        Payment.status == 'completed',
        Payment.payment_method == 'cash'
    ).scalar() or 0.0

    card_payments = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        func.date(Payment.created_at) >= start_date,
        func.date(Payment.created_at) <= end_date,
        Payment.status == 'completed',
        Payment.payment_method == 'card'
    ).scalar() or 0.0

    click_payments = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        func.date(Payment.created_at) >= start_date,
        func.date(Payment.created_at) <= end_date,
        Payment.status == 'completed',
        Payment.payment_method == 'click'
    ).scalar() or 0.0

    payme_payments = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).filter(
        func.date(Payment.created_at) >= start_date,
        func.date(Payment.created_at) <= end_date,
        Payment.status == 'completed',
        Payment.payment_method == 'payme'
    ).scalar() or 0.0

    # 2. Tashriflar soni
    total_visits = Visit.query.filter(
        Visit.visit_date >= start_date,
        Visit.visit_date <= end_date,
        Visit.status == 'allowed'
    ).count()

    # 3. Faol va yangi abonementlar
    new_subs = Subscription.query.filter(
        Subscription.start_date >= start_date,
        Subscription.start_date <= end_date
    ).count()

    payments_list = Payment.query.filter(
        func.date(Payment.created_at) >= start_date,
        func.date(Payment.created_at) <= end_date,
        Payment.status == 'completed'
    ).order_by(Payment.id.desc()).all()

    return render_template(
        'reports/index.html',
        report_type=report_type,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        total_sub_income=total_sub_income,
        total_bar_income=total_bar_income,
        total_income=total_income,
        total_expenses=total_expenses,
        net_profit=net_profit,
        cash_payments=cash_payments,
        card_payments=card_payments,
        click_payments=click_payments,
        payme_payments=payme_payments,
        total_visits=total_visits,
        new_subs=new_subs,
        payments_list=payments_list
    )


@report_bp.route('/export/excel')
@login_required
def export_excel():
    """Moliyaviy hisobotni Excel formatida yuklab olish"""
    start_date_str = request.args.get('start_date', '')
    end_date_str = request.args.get('end_date', '')

    today = date.today()
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date() if start_date_str else date(today.year, today.month, 1)
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date() if end_date_str else today

    payments = Payment.query.filter(
        func.date(Payment.created_at) >= start_date,
        func.date(Payment.created_at) <= end_date,
        Payment.status == 'completed'
    ).order_by(Payment.id.desc()).all()

    headers = ["№", "To'lov raqami", "Sana va vaqt", "Mijoz", "To'lov turi", "Usul", "Summa (so'm)"]
    rows = []
    total_sum = 0.0

    for idx, p in enumerate(payments, 1):
        c_name = p.client.full_name if p.client else "Kassa xaridi"
        rows.append([
            idx,
            p.payment_number,
            p.created_at.strftime('%d.%m.%Y %H:%M'),
            c_name,
            p.type_label,
            p.method_label,
            float(p.amount)
        ])
        total_sum += float(p.amount)

    summary_rows = [
        ("Jami tushum summasi:", f"{int(total_sum):,} so'm".replace(',', ' '))
    ]

    title = f"IRON FITNESS CLUB - Moliyaviy Tushumlar Hisoboti ({start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')})"
    filename = f"Hisobot_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
    out_path = os.path.join(Config.REPORTS_FOLDER, filename)

    export_to_excel(title, headers, rows, out_path, summary_rows)
    return send_file(out_path, as_attachment=True, download_name=filename)
