from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, IntegerField, SelectField, TextAreaField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class TariffForm(FlaskForm):
    name = StringField("Tarif nomi", validators=[DataRequired(message="Tarif nomini kiriting")])
    type = SelectField("Foydalanish turi", choices=[
        ('single', '1 kunlik bir martalik tashrif'),
        ('even_days', '1 oylik - Juft kunlar (2, 4, 6...)'),
        ('odd_days', '1 oylik - Toq kunlar (1, 3, 5...)'),
        ('daily', '1 oylik - Har kuni (Barcha sanalar)')
    ], default='daily')
    duration_days = IntegerField("Amal qilish muddati (kun)", default=30, validators=[DataRequired(), NumberRange(min=1, max=365)])
    price = DecimalField("Narxi (so'm)", default=0, validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField("Tavsif")
    is_active = BooleanField("Faol tarif", default=True)
    submit = SubmitField("Tarifni saqlash")
