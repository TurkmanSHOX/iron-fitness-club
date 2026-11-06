from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DecimalField, IntegerField, SelectField, TextAreaField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class ProductForm(FlaskForm):
    name = StringField("Mahsulot nomi", validators=[DataRequired()])
    barcode = StringField("Shtrix-kod / 2D kod", validators=[DataRequired()])
    category_id = SelectField("Kategoriya", coerce=int)
    supplier_id = SelectField("Yetkazib beruvchi", coerce=int)
    purchase_price = DecimalField("Keltirilgan narxi (so'm)", default=0, validators=[DataRequired(), NumberRange(min=0)])
    sale_price = DecimalField("Sotish narxi (so'm)", default=0, validators=[DataRequired(), NumberRange(min=0)])
    stock_quantity = IntegerField("Boshlang'ich qoldiq", default=0, validators=[NumberRange(min=0)])
    unit = SelectField("O'lchov birligi", choices=[('dona', 'Dona'), ('banka', 'Banka'), ('litr', 'Litr'), ('kg', 'Kg')], default='dona')
    min_stock_alert = IntegerField("Minimal ogohlantirish qoldig'i", default=5, validators=[NumberRange(min=0)])
    expiry_date = DateField("Yaroqlilik muddati", format='%Y-%m-%d', validators=[])
    submit = SubmitField("Mahsulotni saqlash")

class StockIncomeForm(FlaskForm):
    product_id = SelectField("Mahsulot", coerce=int, validators=[DataRequired()])
    quantity = IntegerField("Kirim miqdori", default=1, validators=[DataRequired(), NumberRange(min=1)])
    purchase_price = DecimalField("Yangi kelish narxi (so'm)", validators=[NumberRange(min=0)])
    notes = TextAreaField("Izoh / Kirim hujjati")
    submit = SubmitField("Kirimni tasdiqlash")

class ExpenseForm(FlaskForm):
    title = StringField("Xarajat nomi / maqsadi", validators=[DataRequired()])
    category = SelectField("Kategoriya", choices=[
        ('rent', 'Ijara to\'lovi'),
        ('electricity', 'Elektr energiyasi'),
        ('water', 'Suv va kommunal'),
        ('salary', 'Ish haqi'),
        ('inventory_purchase', 'Mahsulotlar xaridi'),
        ('repair', 'Ta\'mirlash va jihozlar'),
        ('other', 'Boshqa xarajatlar')
    ], default='other')
    amount = DecimalField("Summa (so'm)", validators=[DataRequired(), NumberRange(min=1)])
    payment_method = SelectField("To'lov usuli", choices=[
        ('cash', 'Naqd pul'),
        ('card', 'Bank kartasi'),
        ('bank_transfer', 'Bank o\'tkazmasi')
    ], default='cash')
    expense_date = DateField("Sana", format='%Y-%m-%d', validators=[DataRequired()])
    receipt_image = FileField("Chek / Hujjat rasmi", validators=[FileAllowed(['jpg', 'png', 'jpeg', 'pdf'], "Faqat rasm yoki PDF!")])
    notes = TextAreaField("Qo'shimcha izoh")
    submit = SubmitField("Xarajatni saqlash")
