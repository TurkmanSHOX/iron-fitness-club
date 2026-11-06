from datetime import datetime
from app.extensions import db

class Sale(db.Model):
    __tablename__ = 'sales'

    id = db.Column(db.Integer, primary_key=True)
    sale_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id', ondelete='SET NULL'), nullable=True)
    total_amount = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    discount_amount = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    final_amount = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    cost_amount = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    gross_profit = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    payment_method = db.Column(db.String(20), default='cash', nullable=False)  # cash, card, click, payme
    status = db.Column(db.String(20), default='completed', nullable=False)  # completed, cancelled, refunded
    receipt_pdf_path = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(50), default='admin', nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False, index=True)

    items = db.relationship('SaleItem', backref='sale', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='sale', lazy='dynamic')

    @property
    def formatted_final_amount(self):
        return f"{int(self.final_amount):,} so'm".replace(',', ' ')

    @property
    def payment_method_label(self):
        labels = {
            'cash': 'Naqd pul',
            'card': 'Bank kartasi',
            'click': 'Click',
            'payme': 'Payme'
        }
        return labels.get(self.payment_method, self.payment_method)

    def __repr__(self):
        return f"<Sale {self.sale_number} - {self.final_amount} UZS>"


class SaleItem(db.Model):
    __tablename__ = 'sale_items'

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sales.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    barcode = db.Column(db.String(64), nullable=True)
    purchase_price = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    unit_price = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    total_price = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f"<SaleItem {self.product_name} x{self.quantity}>"
