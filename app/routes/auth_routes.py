from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db
from app.models.admin import Admin
from app.models.setting import AuditLog
from app.forms.auth_forms import LoginForm, ChangePasswordForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data, is_active=True).first()
        if admin and admin.check_password(form.password.data):
            login_user(admin, remember=form.remember_me.data)
            admin.last_login = datetime.now()
            db.session.commit()

            AuditLog.log(
                action='ADMIN_LOGIN',
                admin_id=admin.id,
                details=f"Admin {admin.username} tizimga kirdi",
                ip=request.remote_addr
            )
            flash(f"Xush kelibsiz, {admin.full_name}!", "success")
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
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
            db.session.commit()
            AuditLog.log(
                action='PASSWORD_CHANGED',
                admin_id=current_user.id,
                details="Administrator paroli o'zgartirildi"
            )
            flash("Parolingiz muvaffaqiyatli yangilandi!", "success")
            return redirect(url_for('profile'))
        else:
            flash("Amaldagi joriy parol noto'g'ri!", "danger")

    return render_template('auth/profile.html', form=form)
