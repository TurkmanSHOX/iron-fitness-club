from datetime import datetime
from app.extensions import db

class Tariff(db.Model):
    __tablename__ = 'tariffs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'single', 'even_days', 'odd_days', 'daily'
    duration_days = db.Column(db.Integer, default=30, nullable=False)
    price = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    subscriptions = db.relationship('Subscription', backref='tariff', lazy='dynamic')

    @property
    def type_label(self):
        labels = {
            'single': '1 kunlik tashrif',
            'even_days': 'Juft kunlar (2, 4, 6...)',
            'odd_days': 'Toq kunlar (1, 3, 5...)',
            'daily': 'Har kuni (Cheklovsiz)'
        }
        return labels.get(self.type, self.type)

    @property
    def formatted_price(self):
        return f"{int(self.price):,} so'm".replace(',', ' ')

    def __repr__(self):
        return f"<Tariff {self.name} - {self.price} UZS>"
