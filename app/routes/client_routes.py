import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.config import Config
from app.models.client import Client, ClientQRCode
from app.models.subscription import Subscription
from app.models.payment import Payment
from app.models.visit import Visit
from app.models.sale import Sale
from app.models.setting import AuditLog
from app.forms.client_forms import ClientForm
from app.services.pdf_service import generate_qr_code_image

client_bp = Blueprint('clients', __name__)

@client_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'all')

    query = Client.query

    if search:
        query = query.filter(
            (Client.full_name.ilike(f"%{search}%")) |
            (Client.phone.ilike(f"%{search}%")) |
            (Client.qr_code.ilike(f"%{search}%"))
        )

    if status_filter != 'all':
        query = query.filter(Client.status == status_filter)
    else:
        query = query.filter(Client.status != 'archived')

    pagination = query.order_by(Client.id.desc()).paginate(page=page, per_page=15, error_out=False)
    clients = pagination.items

    return render_template(
        'clients/index.html',
        clients=clients,
        pagination=pagination,
        search=search,
        status_filter=status_filter
    )


@client_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = ClientForm()
    if form.validate_on_submit():
        # Telefon takrorlanishini tekshirish
        clean_phone = form.phone.data.strip().replace(' ', '').replace('-', '')
        existing = Client.query.filter_by(phone=clean_phone).first()
        if existing:
            flash("Ushbu telefon raqamiga ega mijoz allaqachon mavjud!", "danger")
            return render_template('clients/form.html', form=form, title="Yangi mijoz qo'shish")

        # Rasm yuklash
        photo_filename = None
        if form.photo.data:
            f = form.photo.data
            ext = f.filename.rsplit('.', 1)[1].lower()
            photo_filename = f"client_{clean_phone}.{ext}"
            os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'clients'), exist_ok=True)
            f.save(os.path.join(Config.UPLOAD_FOLDER, 'clients', photo_filename))

        # Yagona QR kod yaratish
        qr_token = Client.generate_unique_qr_code()
        
        client = Client(
            full_name=form.full_name.data.strip(),
            phone=clean_phone,
            birth_date=form.birth_date.data,
            gender=form.gender.data,
            photo_url=f"clients/{photo_filename}" if photo_filename else None,
            qr_code=qr_token,
            status='active',
            notes=form.notes.data
        )
        db.session.add(client)
        db.session.flush()

        # QR kod rasmini generatsiya qilish
        qr_img_name = f"qr_{client.id}_{qr_token}.png"
        qr_img_path = os.path.join(Config.QRCODES_FOLDER, qr_img_name)
        generate_qr_code_image(qr_token, qr_img_path)

        qr_rec = ClientQRCode(
            client_id=client.id,
            qr_code_token=qr_token,
            qr_image_path=f"qrcodes/{qr_img_name}",
            is_active=True
        )
        db.session.add(qr_rec)

        AuditLog.log(
            action='CLIENT_CREATED',
            admin_id=current_user.id,
            table='clients',
            target_id=client.id,
            details=f"Mijoz {client.full_name} qo'shildi (QR: {qr_token})"
        )

        db.session.commit()
        flash(f"Mijoz {client.full_name} muvaffaqiyatli ro'yxatga olindi!", "success")
        return redirect(url_for('clients.detail', id=client.id))

    return render_template('clients/form.html', form=form, title="Yangi mijoz qo'shish")


@client_bp.route('/<int:id>')
@login_required
def detail(id):
    client = Client.query.get_or_404(id)
    subscriptions = client.subscriptions.order_by(Subscription.id.desc()).all()
    visits = client.visits.order_by(Visit.id.desc()).limit(20).all()
    payments = client.payments.order_by(Payment.id.desc()).limit(20).all()
    sales = client.sales.order_by(Sale.id.desc()).limit(10).all()
    freeze_requests = client.freeze_requests.order_by(client.freeze_requests.subquery().c.id.desc()).all() if hasattr(client, 'freeze_requests') else []

    return render_template(
        'clients/detail.html',
        client=client,
        subscriptions=subscriptions,
        visits=visits,
        payments=payments,
        sales=sales,
        freeze_requests=freeze_requests
    )


@client_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    client = Client.query.get_or_404(id)
    form = ClientForm(obj=client)

    if form.validate_on_submit():
        clean_phone = form.phone.data.strip().replace(' ', '').replace('-', '')
        existing = Client.query.filter(Client.phone == clean_phone, Client.id != client.id).first()
        if existing:
            flash("Ushbu telefon raqami boshqa mijozga tegishli!", "danger")
            return render_template('clients/form.html', form=form, title="Mijozni tahrirlash", client=client)

        client.full_name = form.full_name.data.strip()
        client.phone = clean_phone
        client.birth_date = form.birth_date.data
        client.gender = form.gender.data
        client.notes = form.notes.data

        if form.photo.data:
            f = form.photo.data
            ext = f.filename.rsplit('.', 1)[1].lower()
            photo_filename = f"client_{clean_phone}.{ext}"
            os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'clients'), exist_ok=True)
            f.save(os.path.join(Config.UPLOAD_FOLDER, 'clients', photo_filename))
            client.photo_url = f"clients/{photo_filename}"

        AuditLog.log(
            action='CLIENT_UPDATED',
            admin_id=current_user.id,
            table='clients',
            target_id=client.id,
            details=f"Mijoz {client.full_name} ma'lumotlari tahrirlandi"
        )

        db.session.commit()
        flash("Mijoz ma'lumotlari yangilandi!", "success")
        return redirect(url_for('clients.detail', id=client.id))

    return render_template('clients/form.html', form=form, title="Mijozni tahrirlash", client=client)


@client_bp.route('/<int:id>/archive', methods=['POST'])
@login_required
def archive(id):
    client = Client.query.get_or_404(id)
    client.status = 'archived'
    AuditLog.log(
        action='CLIENT_ARCHIVED',
        admin_id=current_user.id,
        table='clients',
        target_id=client.id,
        details=f"Mijoz {client.full_name} arxivlandi"
    )
    db.session.commit()
    flash(f"Mijoz {client.full_name} arxivga olindi. Uning barcha to'lov va tashrif tarixi saqlanib qoldi.", "info")
    return redirect(url_for('clients.index'))


@client_bp.route('/<int:id>/qr')
@login_required
def download_qr(id):
    client = Client.query.get_or_404(id)
    qr_img_name = f"qr_{client.id}_{client.qr_code}.png"
    qr_img_path = os.path.join(Config.QRCODES_FOLDER, qr_img_name)
    if not os.path.exists(qr_img_path):
        generate_qr_code_image(client.qr_code, qr_img_path)
    return send_file(qr_img_path, mimetype='image/png', as_attachment=True, download_name=f"QR_{client.full_name}.png")
