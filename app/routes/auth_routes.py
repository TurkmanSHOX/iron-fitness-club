from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.admin import Admin
from app.models.setting import AuditLog
from app.forms.auth_forms import LoginForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.before_app_request
def enforce_password_change():
    """Dastlabki parolni majburiy almashtirish nazorati"""
    if current_user.is_authenticated and not getattr(current_user, 'is_password_changed', True):
        allowed_endpoints = ['auth.profile', 'auth.logout', 'static']
        if request.endpoint and request.endpoint not in allowed_endpoints:
            flash("Xavfsizlik talabi: Tizim xavfsizligi uchun dastlabki parolingizni yangisiga almashtirishingiz shart!", "warning")
            return redirect(url_for('auth.profile'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data, is_active=True).first()
        
        # 1. Hisob vaqtincha bloklanganligini tekshirish
        if admin and admin.is_locked:
            remaining_mins = int((admin.locked_until - datetime.now()).total_seconds() / 60) + 1
            flash(f"Xavfsizlik cheklovi: Ushbu hisob juda ko'p xato urinishlar tufayli vaqtincha bloklangan. Iltimos, {remaining_mins} daqiqadan so'ng qayta urinib ko'ring.", "danger")
            return render_template('auth/login.html', form=form)

        # 2. Parolni tekshirish
        if admin and admin.check_password(form.password.data):
            # Muvaffaqiyatli kirish: xato urinishlarni nolga tushirish
            admin.reset_failed_attempts()
            admin.last_login = datetime.now()
            login_user(admin, remember=form.remember_me.data)
            db.session.commit()

            AuditLog.log(
                action='ADMIN_LOGIN',
                admin_id=admin.id,
                details=f"Admin {admin.username} tizimga kirdi",
                ip=request.remote_addr
            )

            # Majburiy parol almashtirish tekshiruvi
            if not admin.is_password_changed:
                flash("Xush kelibsiz! Xavfsizlik yuzasidan dastlabki parolingizni darhol yangisiga almashtiring.", "warning")
                return redirect(url_for('auth.profile'))

            flash(f"Xush kelibsiz, {admin.full_name}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            if admin:
                is_now_locked = admin.increment_failed_attempts(max_attempts=5, lock_minutes=15)
                db.session.commit()
                if is_now_locked:
                    AuditLog.log(
                        action='LOGIN_LOCKED',
                        admin_id=admin.id,
                        details="5 ta ketma-ket noto'g'ri urinish sababli hisob 15 daqiqaga bloklandi",
                        ip=request.remote_addr
                    )
                    flash("Juda ko'p xato urinishlar! Hisob xavfsizlik sababli 15 daqiqaga bloklandi.", "danger")
                else:
                    attempts_left = 5 - admin.failed_login_attempts
                    flash(f"Login yoki parol noto'g'ri! (Qolgan urinishlar soni: {attempts_left})", "danger")
            else:
                flash("Login yoki parol noto'g'ri!", "danger")

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    AuditLog.log(
        action='ADMIN_LOGOUT',
        admin_id=current_user.id,
        details=f"Admin {current_user.username} tizimdan chiqdi",
        ip=request.remote_addr
    )
    logout_user()
    flash("Tizimdan muvaffaqiyatli chiqdingiz.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.old_password.data):
            current_user.set_password(form.new_password.data)
            current_user.is_password_changed = True
            db.session.commit()
            AuditLog.log(
                action='PASSWORD_CHANGED',
                admin_id=current_user.id,
                details="Administrator paroli muvaffaqiyatli yangilandi"
            )
            flash("Parolingiz muvaffaqiyatli yangilandi! Endi barcha bo'limlardan erkin foydalanishingiz mumkin.", "success")
            return redirect(url_for('auth.profile'))
        else:
            flash("Amaldagi joriy parol noto'g'ri!", "danger")

    return render_template('auth/profile.html', form=form)
