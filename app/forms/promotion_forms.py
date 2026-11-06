from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, IntegerField, SelectField, TextAreaField, DateField, BooleanField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class PromotionForm(FlaskForm):
    title = StringField("Aksiya sarlavhasi", validators=[DataRequired()])
    description = TextAreaField("Tavsif")
    discount_type = SelectField("Chegirma turi", choices=[('percent', 'Foiz (%)'), ('fixed', 'Belgilangan summa (so\'m)')], default='percent')
    discount_value = DecimalField("Chegirma qiymati", validators=[DataRequired(), NumberRange(min=0)])
    start_date = DateField("Boshlanish sanasi", format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField("Tugash sanasi", format='%Y-%m-%d', validators=[DataRequired()])
    target_tariff_id = SelectField("Qaysi tarifga tegishli", coerce=int)
    target_audience = SelectField("Mijozlar toifasi", choices=[('all', 'Barcha mijozlar'), ('new', 'Faqat yangi mijozlar')], default='all')
    max_uses = IntegerField("Maksimal foydalanish soni (ixtiyoriy)", validators=[])
    promo_code = StringField("Promo-kod (ixtiyoriy, masalan: IRON2026)")
    is_active = BooleanField("Faol aksiya", default=True)
    submit = SubmitField("Aksiyani saqlash")
