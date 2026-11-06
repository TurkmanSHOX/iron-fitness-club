from datetime import datetime
from app.extensions import db

class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    payment_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='SET NULL'), nullable=True)
    payment_type = db.Column(db.String(30), nullable=False)  # subscription, single_visit, product_sale, other
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # cash, card, click, payme
    status = db.Column(db.String(20), default='completed', nullable=False)  # pending, completed, failed, refunded
    transaction_id = db.Column(db.String(100), nullable=True)
    receipt_pdf_path = db.Column(db.String(255), nullable=True)
    created_by = db.Column(db.String(50), default='admin', nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)

    transactions = db.relationship('PaymentTransaction', backref='payment', lazy='dynamic')

    @property
    def formatted_amount(self):
        return f"{int(self.amount):,} so'm".replace(',', ' ')

    @property
    def method_label(self):
        labels = {
            'cash': 'Naqd pul',
            'card': 'Bank kartasi',
            'click': 'Click',
            'payme': 'Payme'
        }
        return labels.get(self.payment_method, self.payment_method)

    @property
    def type_label(self):
        labels = {
            'subscription': 'Abonement to\'lovi',
            'single_visit': '1 kunlik tashrif',
            'product_sale': 'Mahsulot savdosi',
            'other': 'Boshqa to\'lov'
        }
        return labels.get(self.payment_type, self.payment_type)

    def __repr__(self):
        return f"<Payment {self.payment_number} - {self.amount} UZS>"


class PaymentTransaction(db.Model):
    __tablename__ = 'payment_transactions'

    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey('payments.id', ondelete='SET NULL'), nullable=True)
    provider = db.Column(db.String(20), nullable=False)  # click, payme
    provider_transaction_id = db.Column(db.String(100), nullable=False, index=True)
    request_payload = db.Column(db.Text, nullable=True)
    response_payload = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False)
    error_message = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<PaymentTransaction {self.provider} tx:{self.provider_transaction_id}>"
