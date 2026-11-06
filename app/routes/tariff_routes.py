from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.tariff import Tariff
from app.models.setting import AuditLog
from app.forms.tariff_forms import TariffForm

tariff_bp = Blueprint('tariffs', __name__)

@tariff_bp.route('/')
@login_required
def index():
    tariffs = Tariff.query.order_by(Tariff.id.asc()).all()
    return render_template('tariffs/index.html', tariffs=tariffs)


@tariff_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = TariffForm()
    if form.validate_on_submit():
        tariff = Tariff(
            name=form.name.data.strip(),
            type=form.type.data,
            duration_days=form.duration_days.data,
            price=form.price.data,
            description=form.description.data,
            is_active=form.is_active.data
        )
        db.session.add(tariff)
        db.session.flush()

        AuditLog.log(
            action='TARIFF_CREATED',
            admin_id=current_user.id,
            table='tariffs',
            target_id=tariff.id,
            details=f"Yangi tarif {tariff.name} yaratildi ({tariff.price} UZS)"
        )

        db.session.commit()
        flash(f"Tarif '{tariff.name}' muvaffaqiyatli yaratildi!", "success")
        return redirect(url_for('tariffs.index'))

    return render_template('tariffs/form.html', form=form, title="Yangi tarif yaratish")


@tariff_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    tariff = Tariff.query.get_or_404(id)
    form = TariffForm(obj=tariff)

    if form.validate_on_submit():
        old_price = tariff.price
        tariff.name = form.name.data.strip()
        tariff.type = form.type.data
        tariff.duration_days = form.duration_days.data
        tariff.price = form.price.data
        tariff.description = form.description.data
        tariff.is_active = form.is_active.data

        AuditLog.log(
            action='TARIFF_UPDATED',
            admin_id=current_user.id,
            table='tariffs',
            target_id=tariff.id,
            details=f"Tarif {tariff.name} tahrirlandi. Narx: {old_price} -> {tariff.price} UZS. (Avvalgi xaridlarga ta'sir qilmaydi)"
        )

        db.session.commit()
        flash(f"Tarif '{tariff.name}' yangilandi! Eslatma: yangi narx faqat kelgusi xaridlarga qo'llanadi.", "success")
        return redirect(url_for('tariffs.index'))

    return render_template('tariffs/form.html', form=form, title="Tarifni tahrirlash", tariff=tariff)


@tariff_bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle(id):
    tariff = Tariff.query.get_or_404(id)
    tariff.is_active = not tariff.is_active
    status_str = "faollashtirildi" if tariff.is_active else "nofaol qilindi"

    AuditLog.log(
        action='TARIFF_TOGGLED',
        admin_id=current_user.id,
        table='tariffs',
        target_id=tariff.id,
        details=f"Tarif {tariff.name} {status_str}"
    )

    db.session.commit()
    flash(f"Tarif '{tariff.name}' {status_str}!", "info")
    return redirect(url_for('tariffs.index'))
