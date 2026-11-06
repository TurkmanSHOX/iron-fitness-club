from datetime import date, datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.visit import Visit, AccessAttempt
from app.models.client import Client
from app.services.access_service import check_in_client

visit_bp = Blueprint('visits', __name__)

@visit_bp.route('/scanner')
@login_required
def scanner():
    """Reception uchun 2D QR va Shtrix-kod skanlash asosiy oynasi"""
    today = date.today()
    today_visits = Visit.query.filter_by(visit_date=today).order_by(Visit.id.desc()).limit(15).all()
    today_allowed_count = Visit.query.filter_by(visit_date=today, status='allowed').count()
    today_denied_count = Visit.query.filter_by(visit_date=today, status='denied').count()

    return render_template(
        'visits/scanner.html',
        today_visits=today_visits,
        today_allowed_count=today_allowed_count,
        today_denied_count=today_denied_count,
        today_date=today.strftime('%d.%m.%Y')
    )


@visit_bp.route('/api/checkin', methods=['POST'])
@login_required
def checkin_api():
    """
    2D Barcode / QR skanerdan kelgan so'rovni tekshirish va javob berish.
    JSON qabul qiladi: { "qr_code": "IFC-...", "override_reason": "..." }
    """
    data = request.get_json() or {}
    qr_code = data.get('qr_code', '').strip()
    override_reason = data.get('override_reason', '').strip() or None

    if not qr_code:
        return jsonify({
            'success': False,
            'status': 'denied',
            'reason': "QR-kod ma'lumoti bo'sh!",
            'color': 'danger'
        }), 400

    result = check_in_client(
        qr_token_or_client_id=qr_code,
        scan_type='manual' if override_reason else 'qr',
        admin_id=current_user.id,
        override_reason=override_reason
    )

    client_data = None
    sub_data = None
    if result.get('client'):
        c = result['client']
        client_data = {
            'id': c.id,
            'full_name': c.full_name,
            'phone': c.phone,
            'photo_url': f"/uploads/{c.photo_url}" if c.photo_url else None
        }

    if result.get('subscription'):
        s = result['subscription']
        sub_data = {
            'tariff_name': s.tariff.name,
            'start_date': s.start_date.strftime('%d.%m.%Y'),
            'end_date': s.end_date.strftime('%d.%m.%Y'),
            'days_left': s.days_left,
            'status_label': s.status_label
        }

    return jsonify({
        'success': result['success'],
        'status': result['status'],
        'color': result['color'],
        'reason': result['reason'],
        'client': client_data,
        'subscription': sub_data,
        'visit_time': datetime.now().strftime('%H:%M:%S')
    })


@visit_bp.route('/manual', methods=['GET', 'POST'])
@login_required
def manual_checkin():
    """Qo'lda mijozni qidirib kirishni qayd etish (istisno sababi bilan)"""
    clients = Client.query.filter_by(status='active').order_by(Client.full_name.asc()).all()

    if request.method == 'POST':
        client_id = request.form.get('client_id', type=int)
        override_reason = request.form.get('override_reason', '').strip() or None

        if not client_id:
            flash("Mijoz tanlanmadi!", "warning")
            return redirect(url_for('visits.manual_checkin'))

        result = check_in_client(
            qr_token_or_client_id=client_id,
            scan_type='manual',
            admin_id=current_user.id,
            override_reason=override_reason
        )

        if result['success']:
            flash(f"Kirish qayd etildi: {result['reason']}", result['color'])
            return redirect(url_for('visits.scanner'))
        else:
            flash(f"Kirish rad etildi: {result['reason']}", "danger")

    return render_template('visits/manual.html', clients=clients)


@visit_bp.route('/history')
@login_required
def history():
    """Barcha tashriflar tarixi"""
    page = request.args.get('page', 1, type=int)
    date_filter = request.args.get('date', '').strip()
    status_filter = request.args.get('status', 'all')

    query = Visit.query.join(Client)

    if date_filter:
        try:
            d = datetime.strptime(date_filter, '%Y-%m-%d').date()
            query = query.filter(Visit.visit_date == d)
        except Exception:
            pass

    if status_filter != 'all':
        query = query.filter(Visit.status == status_filter)

    pagination = query.order_by(Visit.id.desc()).paginate(page=page, per_page=20, error_out=False)
    visits = pagination.items

    return render_template(
        'visits/history.html',
        visits=visits,
        pagination=pagination,
        date_filter=date_filter,
        status_filter=status_filter
    )
