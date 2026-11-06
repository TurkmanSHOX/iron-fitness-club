from datetime import datetime, date
from app.extensions import db

class Promotion(db.Model):
    __tablename__ = 'promotions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    discount_type = db.Column(db.String(20), default='percent', nullable=False)  # percent, fixed
    discount_value = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    target_tariff_id = db.Column(db.Integer, db.ForeignKey('tariffs.id', ondelete='SET NULL'), nullable=True)
    target_audience = db.Column(db.String(20), default='all', nullable=False)  # all, new
    max_uses = db.Column(db.Integer, nullable=True)
    current_uses = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    promo_codes = db.relationship('PromoCode', backref='promotion', lazy='dynamic', cascade='all, delete-orphan')
    tariff = db.relationship('Tariff', foreign_keys=[target_tariff_id])

    @property
    def is_currently_valid(self):
        today = date.today()
        if not self.is_active:
            return False
        if today < self.start_date or today > self.end_date:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True

    def calculate_discount(self, original_amount):
        """Chegirma summasini hisoblab beradi"""
        if not self.is_currently_valid:
            return 0.00
        if self.discount_type == 'percent':
            discount = float(original_amount) * (float(self.discount_value) / 100.0)
            return min(discount, float(original_amount))
        elif self.discount_type == 'fixed':
            return min(float(self.discount_value), float(original_amount))
        return 0.00

    def __repr__(self):
        return f"<Promotion {self.title}>"


class PromoCode(db.Model):
    __tablename__ = 'promo_codes'

    id = db.Column(db.Integer, primary_key=True)
    promotion_id = db.Column(db.Integer, db.ForeignKey('promotions.id', ondelete='CASCADE'), nullable=False)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    is_used = db.Column(db.Boolean, default=False, nullable=False)
    used_by_client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='SET NULL'), nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)

    client = db.relationship('Client', foreign_keys=[used_by_client_id])

    def __repr__(self):
        return f"<PromoCode {self.code}>"
