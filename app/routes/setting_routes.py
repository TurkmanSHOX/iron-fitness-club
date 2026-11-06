import os
import shutil
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.config import Config
from app.models.setting import Setting, AuditLog, BackupLog

setting_bp = Blueprint('settings', __name__)

@setting_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == 'POST':
        # Sozlamalarni yangilash
        club_name = request.form.get('club_name', 'IRON FITNESS CLUB').strip()
        club_phone = request.form.get('club_phone', '').strip()
        club_address = request.form.get('club_address', '').strip()
        max_freeze_days = request.form.get('max_freeze_days', '10').strip()
        max_freeze_per_period = request.form.get('max_freeze_per_period', '1').strip()
        single_entry = 'true' if request.form.get('single_entry_per_day') else 'false'
        tg_token = request.form.get('telegram_bot_token', '').strip()
        click_merchant_id = request.form.get('click_merchant_id', '').strip()
        click_service_id = request.form.get('click_service_id', '').strip()
        click_secret_key = request.form.get('click_secret_key', '').strip()
        payme_merchant_id = request.form.get('payme_merchant_id', '').strip()
        payme_secret_key = request.form.get('payme_secret_key', '').strip()

        Setting.set_value('club_name', club_name, "Sport klubi nomi")
        Setting.set_value('club_phone', club_phone, "Aloqa telefoni")
        Setting.set_value('club_address', club_address, "Manzil")
        Setting.set_value('max_freeze_days', max_freeze_days, "Maksimal muzlatish kuni")
        Setting.set_value('max_freeze_per_period', max_freeze_per_period, "Davrdagi muzlatishlar soni")
        Setting.set_value('single_entry_per_day', single_entry, "Bir kunda bir marta kirish")
        
        if tg_token:
            Setting.set_value('telegram_bot_token', tg_token, "Telegram bot tokeni")
        if click_merchant_id:
            Setting.set_value('click_merchant_id', click_merchant_id, "Click Merchant ID")
        if click_service_id:
            Setting.set_value('click_service_id', click_service_id, "Click Service ID")
        if click_secret_key:
            Setting.set_value('click_secret_key', click_secret_key, "Click Secret Key")
        if payme_merchant_id:
            Setting.set_value('payme_merchant_id', payme_merchant_id, "Payme Merchant ID")
        if payme_secret_key:
            Setting.set_value('payme_secret_key', payme_secret_key, "Payme Secret Key")

        AuditLog.log(
            action='SETTINGS_UPDATED',
            admin_id=current_user.id,
            details="Tizim sozlamalari yangilandi"
        )

        flash("Tizim sozlamalari muvaffaqiyatli saqlandi!", "success")
        return redirect(url_for('settings.index'))

    # Joriy sozlamalar
    settings_dict = {
        'club_name': Setting.get_value('club_name', 'IRON FITNESS CLUB'),
        'club_phone': Setting.get_value('club_phone', '+998 90 123 45 67'),
        'club_address': Setting.get_value('club_address', 'Urganch shahri, Al-Xorazmiy ko\'chasi, 24-uy'),
        'max_freeze_days': Setting.get_value('max_freeze_days', '10'),
        'max_freeze_per_period': Setting.get_value('max_freeze_per_period', '1'),
        'single_entry_per_day': Setting.get_value('single_entry_per_day', 'true') == 'true',
        'telegram_bot_token': Setting.get_value('telegram_bot_token', Config.TELEGRAM_BOT_TOKEN),
        'click_merchant_id': Setting.get_value('click_merchant_id', Config.CLICK_MERCHANT_ID),
        'click_service_id': Setting.get_value('click_service_id', Config.CLICK_SERVICE_ID),
        'click_secret_key': Setting.get_value('click_secret_key', Config.CLICK_SECRET_KEY),
        'payme_merchant_id': Setting.get_value('payme_merchant_id', Config.PAYME_MERCHANT_ID),
        'payme_secret_key': Setting.get_value('payme_secret_key', Config.PAYME_SECRET_KEY),
    }

    backups = BackupLog.query.order_by(BackupLog.id.desc()).limit(10).all()

    return render_template('settings/index.html', settings=settings_dict, backups=backups)


@setting_bp.route('/backup/create', methods=['POST'])
@login_required
def create_backup():
    """Qo'lda zaxira nusxa yaratish"""
    try:
        from scripts.backup import make_backup
        success, res = make_backup(backup_type='manual', compress=True)
        if success:
            filename = os.path.basename(res)
            AuditLog.log(
                action='MANUAL_BACKUP_CREATED',
                admin_id=current_user.id,
                details=f"Zaxira nusxa yaratildi: {filename}"
            )
            flash(f"Zaxira nusxa '{filename}' muvaffaqiyatli yaratildi!", "success")
        else:
            flash(f"Zaxiralashda xatolik: {res}", "danger")
    except Exception as e:
        flash(f"Zaxiralashda xatolik: {e}", "danger")

    return redirect(url_for('settings.index'))


@setting_bp.route('/backup/download/<filename>')
@login_required
def download_backup(filename):
    """Zaxira nusxani yuklab olish"""
    safe_name = os.path.basename(filename)
    path = os.path.join(Config.BACKUPS_FOLDER, safe_name)
    if not os.path.exists(path):
        flash("Zaxira nusxa fayli topilmadi", "danger")
        return redirect(url_for('settings.index'))
    return send_file(path, as_attachment=True, download_name=safe_name)


@setting_bp.route('/audit')
@login_required
def audit_logs():
    """Audit jurnali"""
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.id.desc()).paginate(page=page, per_page=25, error_out=False)
    return render_template('settings/audit.html', logs=logs.items, pagination=logs)
