from datetime import datetime, date
from app.extensions import db

class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    tariff_id = db.Column(db.Integer, db.ForeignKey('tariffs.id', ondelete='RESTRICT'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    original_price = db.Column(db.Numeric(14, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    status = db.Column(db.String(20), default='active', nullable=False, index=True)  # active, expired, frozen, cancelled
    freeze_count = db.Column(db.Integer, default=0, nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    history = db.relationship('SubscriptionHistory', backref='subscription', lazy='dynamic', cascade='all, delete-orphan')
    freeze_requests = db.relationship('FreezeRequest', backref='subscription', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='subscription', lazy='dynamic')
    visits = db.relationship('Visit', backref='subscription', lazy='dynamic')

    @property
    def days_left(self):
        today = date.today()
        if self.status == 'frozen':
            return (self.end_date - self.start_date).days
        if today > self.end_date:
            return 0
        return (self.end_date - today).days

    @property
    def status_label(self):
        labels = {
            'active': 'Faol',
            'expired': 'Muddati tugagan',
            'frozen': 'Muzlatilgan',
            'cancelled': 'Bekor qilingan'
        }
        return labels.get(self.status, self.status)

    @property
    def status_badge_class(self):
        badges = {
            'active': 'bg-success',
            'expired': 'bg-danger',
            'frozen': 'bg-info text-dark',
            'cancelled': 'bg-secondary'
        }
        return badges.get(self.status, 'bg-light text-dark')

    def is_day_allowed(self, check_date=None):
        """Bugungi sana ushbu abonement tarifiga mos kelishini tekshiradi"""
        if check_date is None:
            check_date = date.today()

        if self.status != 'active':
            return False, f"Abonement holati: {self.status_label}"

        if check_date < self.start_date:
            return False, f"Abonement {self.start_date.strftime('%d.%m.%Y')} sanasidan boshlanadi"

        if check_date > self.end_date:
            return False, f"Abonement muddati tugagan ({self.end_date.strftime('%d.%m.%Y')})"

        tariff_type = self.tariff.type
        day_num = check_date.day

        if tariff_type == 'daily':
            return True, "Har kunlik tarif"
        elif tariff_type == 'even_days':
            if day_num % 2 == 0:
                return True, f"Juft kun ({day_num}-sana)"
            return False, f"Bugun toq sana ({day_num}-sana). Sizning tarifingiz: Juft kunlar"
        elif tariff_type == 'odd_days':
            if day_num % 2 != 0:
                return True, f"Toq kun ({day_num}-sana)"
            return False, f"Bugun juft sana ({day_num}-sana). Sizning tarifingiz: Toq kunlar"
        elif tariff_type == 'single':
            if check_date == self.start_date:
                return True, "1 kunlik bir martalik tashrif"
            return False, "1 kunlik tashrif muddati o'tgan"

        return False, "Noma'lum tarif turi"

    def __repr__(self):
        return f"<Subscription {self.id} - Client {self.client_id} ({self.status})>"


class SubscriptionHistory(db.Model):
    __tablename__ = 'subscription_history'

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String(30), nullable=False)  # created, renewed, tariff_changed, frozen, unfrozen, cancelled
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=True)
    old_end_date = db.Column(db.Date, nullable=True)
    new_end_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(50), default='system', nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<SubscriptionHistory {self.action} on Sub {self.subscription_id}>"


class FreezeRequest(db.Model):
    __tablename__ = 'freeze_requests'

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id', ondelete='CASCADE'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    days_count = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)  # pending, approved, rejected
    admin_comment = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='SET NULL'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    reviewer = db.relationship('Admin', foreign_keys=[reviewed_by])

    @property
    def status_label(self):
        labels = {
            'pending': 'Kutilmoqda',
            'approved': 'Tasdiqlangan',
            'rejected': 'Rad etilgan'
        }
        return labels.get(self.status, self.status)

    def __repr__(self):
        return f"<FreezeRequest {self.id} ({self.status}) for Sub {self.subscription_id}>"
