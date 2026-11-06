from datetime import datetime
from app.extensions import db

class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=True)
    telegram_id = db.Column(db.BigInteger, nullable=False, index=True)
    message_type = db.Column(db.String(30), nullable=False)  # sub_expiring_3days, sub_expiring_1day, sub_expired, payment_success, freeze_update, promo, receipt
    message_text = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)  # pending, sent, failed
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<Notification {self.message_type} -> {self.telegram_id} ({self.status})>"
