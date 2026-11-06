from datetime import datetime
from app.extensions import db

class ProductCategory(db.Model):
    __tablename__ = 'product_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    products = db.relationship('Product', backref='category', lazy='dynamic')

    def __repr__(self):
        return f"<Category {self.name}>"


class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    contact_person = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    products = db.relationship('Product', backref='supplier', lazy='dynamic')

    def __repr__(self):
        return f"<Supplier {self.name}>"


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id', ondelete='SET NULL'), nullable=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('suppliers.id', ondelete='SET NULL'), nullable=True)
    name = db.Column(db.String(150), nullable=False)
    barcode = db.Column(db.String(64), unique=True, nullable=False, index=True)
    purchase_price = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    sale_price = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False, index=True)
    unit = db.Column(db.String(20), default='dona', nullable=False)
    min_stock_alert = db.Column(db.Integer, default=5, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    movements = db.relationship('StockMovement', backref='product', lazy='dynamic')
    sale_items = db.relationship('SaleItem', backref='product', lazy='dynamic')

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_alert

    @property
    def formatted_sale_price(self):
        return f"{int(self.sale_price):,} so'm".replace(',', ' ')

    @property
    def formatted_purchase_price(self):
        return f"{int(self.purchase_price):,} so'm".replace(',', ' ')

    def __repr__(self):
        return f"<Product {self.name} ({self.barcode})>"


class StockMovement(db.Model):
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='RESTRICT'), nullable=False, index=True)
    movement_type = db.Column(db.String(30), nullable=False, index=True)  # in, out_sale, return, write_off, inventory_adjustment
    quantity = db.Column(db.Integer, nullable=False)
    previous_stock = db.Column(db.Integer, nullable=False)
    new_stock = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    total_amount = db.Column(db.Numeric(14, 2), default=0.00, nullable=False)
    reference_id = db.Column(db.String(50), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(50), default='admin', nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    @property
    def type_label(self):
        labels = {
            'in': 'Kirim (Xarid)',
            'out_sale': 'Chiqim (Sotuv)',
            'return': 'Qaytarish (Vozvrat)',
            'write_off': 'Hisobdan chiqarish (Spisanie)',
            'inventory_adjustment': 'Inventarizatsiya tuzatishi'
        }
        return labels.get(self.movement_type, self.movement_type)

    def __repr__(self):
        return f"<StockMovement {self.movement_type} {self.quantity} for Prod {self.product_id}>"
