from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.subscription import Subscription, FreezeRequest
from app.models.client import Client
from app.models.tariff import Tariff
from app.models.setting import Setting
from app.services.subscription_service import create_subscription
from app.services.freeze_service import approve_freeze_request, reject_freeze_request

subscription_bp = Blueprint('subscriptions', __name__)

@subscription_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()

    query = Subscription.query.join(Client)

    if search:
        query = query.filter(
            (Client.full_name.ilike(f"%{search}%")) |
            (Client.phone.ilike(f"%{search}%"))
        )

    if status_filter != 'all':
        query = query.filter(Subscription.status == status_filter)

    pagination = query.order_by(Subscription.id.desc()).paginate(page=page, per_page=15, error_out=False)
    subscriptions = pagination.items

    return render_template(
        'subscriptions/index.html',
        subscriptions=subscriptions,
        pagination=pagination,
        status_filter=status_filter,
        search=search
    )


@subscription_bp.route('/sell', methods=['GET', 'POST'])
@login_required
def sell():
    client_id = request.args.get('client_id', type=int)
    clients = Client.query.filter_by(status='active').order_by(Client.full_name.asc()).all()
    tariffs = Tariff.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        selected_client_id = request.form.get('client_id', type=int)
        tariff_id = request.form.get('tariff_id', type=int)
        payment_method = request.form.get('payment_method', 'cash')
        start_date = request.form.get('start_date') or str(date.today())
        discount_amount = float(request.form.get('discount_amount', 0))
        paid_amount = float(request.form.get('paid_amount', 0))
        notes = request.form.get('notes')

        try:
            sub = create_subscription(
                client_id=selected_client_id,
                tariff_id=tariff_id,
                payment_method=payment_method,
                paid_amount=paid_amount if paid_amount > 0 else None,
                start_date=start_date,
                discount_amount=discount_amount,
                notes=notes,
                created_by=current_user.username
            )
            flash(f"Abonement muvaffaqiyatli rasmiylashtirildi! (Amal qilish: {sub.start_date.strftime('%d.%m.%Y')} - {sub.end_date.strftime('%d.%m.%Y')})", "success")
            return redirect(url_for('clients.detail', id=selected_client_id))
        except Exception as e:
            flash(f"Xatolik yuz berdi: {str(e)}", "danger")

    return render_template(
        'subscriptions/sell.html',
        clients=clients,
        tariffs=tariffs,
        selected_client_id=client_id,
        today=date.today().strftime('%Y-%m-%d')
    )


@subscription_bp.route('/freeze_requests')
@login_required
def freeze_requests():
    status_filter = request.args.get('status', 'pending')
    query = FreezeRequest.query
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    requests_list = query.order_by(FreezeRequest.id.desc()).all()
    max_days = Setting.get_value('max_freeze_days', '10')

    return render_template(
        'subscriptions/freeze_requests.html',
        requests_list=requests_list,
        status_filter=status_filter,
        max_days=max_days
    )


@subscription_bp.route('/freeze_requests/<int:id>/approve', methods=['POST'])
@login_required
def approve_freeze(id):
    comment = request.form.get('admin_comment', '').strip()
    success, msg = approve_freeze_request(id, current_user.id, comment)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(url_for('subscriptions.freeze_requests'))


@subscription_bp.route('/freeze_requests/<int:id>/reject', methods=['POST'])
@login_required
def reject_freeze(id):
    comment = request.form.get('admin_comment', '').strip()
    success, msg = reject_freeze_request(id, current_user.id, comment)
    if success:
        flash(msg, "warning")
    else:
        flash(msg, "danger")
    return redirect(url_for('subscriptions.freeze_requests'))
