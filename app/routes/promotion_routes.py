from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.promotion import Promotion, PromoCode
from app.models.tariff import Tariff
from app.models.setting import AuditLog
from app.forms.promotion_forms import PromotionForm

promotion_bp = Blueprint('promotions', __name__)

@promotion_bp.route('/')
@login_required
def index():
    promotions = Promotion.query.order_by(Promotion.id.desc()).all()
    return render_template('promotions/index.html', promotions=promotions)


@promotion_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = PromotionForm()
    tariffs = Tariff.query.filter_by(is_active=True).all()
    form.target_tariff_id.choices = [(0, 'Barcha tariflar')] + [(t.id, t.name) for t in tariffs]

    if form.validate_on_submit():
        promo = Promotion(
            title=form.title.data.strip(),
            description=form.description.data,
            discount_type=form.discount_type.data,
            discount_value=form.discount_value.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            target_tariff_id=form.target_tariff_id.data if form.target_tariff_id.data > 0 else None,
            target_audience=form.target_audience.data,
            max_uses=form.max_uses.data,
            is_active=form.is_active.data
        )
        db.session.add(promo)
        db.session.flush()

        # Agar promo-kod ko'rsatilgan bo'lsa
        if form.promo_code.data:
            clean_code = form.promo_code.data.strip().upper()
            code_obj = PromoCode(
                promotion_id=promo.id,
                code=clean_code,
                is_used=False
            )
            db.session.add(code_obj)

        AuditLog.log(
            action='PROMOTION_CREATED',
            admin_id=current_user.id,
            table='promotions',
            target_id=promo.id,
            details=f"Aksiya '{promo.title}' yaratildi"
        )

        db.session.commit()
        flash(f"Aksiya '{promo.title}' muvaffaqiyatli e'lon qilindi!", "success")
        return redirect(url_for('promotions.index'))

    return render_template('promotions/form.html', form=form, title="Yangi aksiya yaratish")


@promotion_bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle(id):
    promo = Promotion.query.get_or_404(id)
    promo.is_active = not promo.is_active
    db.session.commit()
    flash(f"Aksiya '{promo.title}' holati o'zgartirildi!", "info")
    return redirect(url_for('promotions.index'))
