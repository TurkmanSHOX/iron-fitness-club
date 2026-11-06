from datetime import datetime
import secrets
from app.extensions import db

class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    birth_date = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), default='male', nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    qr_code = db.Column(db.String(64), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), default='active', nullable=False, index=True)  # active, inactive, archived
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Relationships
    subscriptions = db.relationship('Subscription', backref='client', lazy='dynamic', cascade='all, delete-orphan')
    visits = db.relationship('Visit', backref='client', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='client', lazy='dynamic', cascade='all, delete-orphan')
    sales = db.relationship('Sale', backref='client', lazy='dynamic')
    telegram_user = db.relationship('TelegramUser', backref='client', uselist=False)
    qr_tokens = db.relationship('ClientQRCode', backref='client', lazy='dynamic', cascade='all, delete-orphan')
    freeze_requests = db.relationship('FreezeRequest', backref='client', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def active_subscription(self):
        """Mijozning ayni paytdagi faol yoki muzlatilgan abonementini qaytaradi"""
        from app.models.subscription import Subscription
        return Subscription.query.filter(
            Subscription.client_id == self.id,
            Subscription.status.in_(['active', 'frozen'])
        ).order_by(Subscription.id.desc()).first()

    @staticmethod
    def generate_unique_qr_code():
        """Xavfsiz, yagona 16 belgili QR identifikator ishlab chiqarish"""
        token = "IFC-" + secrets.token_hex(8).upper()
        return token

    def __repr__(self):
        return f"<Client {self.full_name} ({self.phone})>"


class ClientQRCode(db.Model):
    __tablename__ = 'client_qr_codes'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    qr_code_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    qr_image_path = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<ClientQRCode {self.qr_code_token}>"


class TelegramUser(db.Model):
    __tablename__ = 'telegram_users'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='SET NULL'), nullable=True)
    telegram_id = db.Column(db.BigInteger, unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), nullable=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True, index=True)
    step = db.Column(db.String(50), default='start', nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    def __repr__(self):
        return f"<TelegramUser {self.telegram_id}>"
