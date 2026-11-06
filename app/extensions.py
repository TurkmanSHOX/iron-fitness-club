from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler
import pytz

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = "Iltimos, avval tizimga kiring."
login_manager.login_message_category = "warning"

tashkent_tz = pytz.timezone('Asia/Tashkent')
scheduler = BackgroundScheduler(timezone=tashkent_tz)
