from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    username = StringField("Foydalanuvchi nomi", validators=[DataRequired(message="Loginni kiriting"), Length(min=3, max=50)])
    password = PasswordField("Parol", validators=[DataRequired(message="Parolni kiriting")])
    remember_me = BooleanField("Eslab qolish")
    submit = SubmitField("Tizimga kirish")

class ChangePasswordForm(FlaskForm):
    old_password = PasswordField("Joriy parol", validators=[DataRequired()])
    new_password = PasswordField("Yangi parol", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Parolni yangilash")
