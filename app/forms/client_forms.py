from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class ClientForm(FlaskForm):
    full_name = StringField("F.I.Sh.", validators=[DataRequired(message="Ism-familiyani kiriting"), Length(max=100)])
    phone = StringField("Telefon raqami", validators=[DataRequired(message="Telefon raqamini kiriting"), Length(min=9, max=20)])
    birth_date = DateField("Tug'ilgan sana", format='%Y-%m-%d', validators=[])
    gender = SelectField("Jinsi", choices=[('male', 'Erkak'), ('female', 'Ayol')], default='male')
    photo = FileField("Mijoz rasmi", validators=[FileAllowed(['jpg', 'png', 'jpeg'], "Faqat rasm fayllari!")])
    notes = TextAreaField("Qo'shimcha izoh")
    submit = SubmitField("Saqlash")
