from datetime import datetime, date, time
from app.extensions import db

class Visit(db.Model):
    __tablename__ = 'visits'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False, index=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True)
    visit_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    visit_time = db.Column(db.Time, default=lambda: datetime.now().time(), nullable=False)
    scan_type = db.Column(db.String(20), default='qr', nullable=False)  # 'qr', 'manual'
    status = db.Column(db.String(20), default='allowed', nullable=False, index=True)  # 'allowed', 'denied'
    denial_reason = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.String(255), nullable=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('admins.id', ondelete='SET NULL'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    admin = db.relationship('Admin', foreign_keys=[admin_id])

    @property
    def formatted_time(self):
        return self.visit_time.strftime('%H:%M:%S')

    @property
    def formatted_date(self):
        return self.visit_date.strftime('%d.%m.%Y')

    def __repr__(self):
        return f"<Visit {self.id} - Client {self.client_id} ({self.status})>"


class AccessAttempt(db.Model):
    __tablename__ = 'access_attempts'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, nullable=True)
    qr_code = db.Column(db.String(64), nullable=True, index=True)
    status = db.Column(db.String(20), nullable=False)  # 'allowed', 'denied'
    reason = db.Column(db.String(255), nullable=True)
    scanned_at = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)

    def __repr__(self):
        return f"<AccessAttempt {self.qr_code} ({self.status})>"
