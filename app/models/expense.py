from datetime import datetime, date
from app.extensions import db

class Expense(db.Model):
    __tablename__ = 'expenses'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(30), nullable=False, index=True)  # rent, electricity, water, salary, inventory_purchase, repair, other
    title = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Numeric(14, 2), nullable=False)
    payment_method = db.Column(db.String(20), default='cash', nullable=False)  # cash, card, bank_transfer
    expense_date = db.Column(db.Date, default=date.today, nullable=False, index=True)
    receipt_image = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(50), default='admin', nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    @property
    def formatted_amount(self):
        return f"{int(self.amount):,} so'm".replace(',', ' ')

    @property
    def category_label(self):
        labels = {
            'rent': 'Ijara to\'lovi',
            'electricity': 'Elektr energiyasi',
            'water': 'Suv va kommunal',
            'salary': 'Ish haqi',
            'inventory_purchase': 'Mahsulotlar xaridi',
            'repair': 'Ta\'mirlash va jihozlar',
            'other': 'Boshqa xarajatlar'
        }
        return labels.get(self.category, self.category)

    def __repr__(self):
        return f"<Expense {self.title} - {self.amount} UZS>"
