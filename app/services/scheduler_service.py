import os
import shutil
from datetime import date, datetime, timedelta
from app.extensions import db, scheduler
from app.models.subscription import Subscription
from app.models.notification import Notification
from app.models.setting import BackupLog
from app.services.freeze_service import auto_unfreeze_expired_subscriptions
from app.services.telegram_service import send_telegram_message

def check_and_notify_expiring_subscriptions(app):
    """
    Texnik topshiriqning 10.5-bandi:
    Abonement muddati tugashiga 3 kun, 1 kun qolganda va tugagan kuni avtomatik eslatma yuborish.
    Bir xil eslatma takror yuborilmaydi.
    """
    with app.app_context():
        today = date.today()
        # 1. 3 kun qolganlar
        target_3days = today + timedelta(days=3)
        subs_3days = Subscription.query.filter(
            Subscription.status == 'active',
            Subscription.end_date == target_3days
        ).all()

        for sub in subs_3days:
            _send_unique_reminder(
                sub=sub,
                msg_type='sub_expiring_3days',
                text=(
                    f"⚠️ <b>Hurmatli {sub.client.full_name}!</b>\n\n"
                    f"Sizning <b>«{sub.tariff.name}»</b> abonementingiz tugashiga <b>3 kun</b> qoldi.\n"
                    f"🏁 Tugash sanasi: <b>{sub.end_date.strftime('%d.%m.%Y')}</b>\n\n"
                    f"Mashg'ulotlaringiz uzilib qolmasligi uchun uni bot orqali uzaytirishingiz yoki tarifni yangilashingiz mumkin!"
                )
            )

        # 2. 1 kun qolganlar
        target_1day = today + timedelta(days=1)
        subs_1day = Subscription.query.filter(
            Subscription.status == 'active',
            Subscription.end_date == target_1day
        ).all()

        for sub in subs_1day:
            _send_unique_reminder(
                sub=sub,
                msg_type='sub_expiring_1day',
                text=(
                    f"⏳ <b>Hurmatli {sub.client.full_name}!</b>\n\n"
                    f"Abonementingiz ertaga, ya'ni <b>{sub.end_date.strftime('%d.%m.%Y')}</b> sanasida tugaydi!\n\n"
                    f"Sport zali xizmatlaridan uzluksiz foydalanish uchun bugunoq to'lov qilib uzaytirishni tavsiya qilamiz."
                )
            )

        # 3. Bugun tugaganlar
        subs_today = Subscription.query.filter(
            Subscription.status == 'active',
            Subscription.end_date < today
        ).all()

        for sub in subs_today:
            sub.status = 'expired'
            db.session.commit()
            _send_unique_reminder(
                sub=sub,
                msg_type='sub_expired',
                text=(
                    f"🛑 <b>Hurmatli {sub.client.full_name}!</b>\n\n"
                    f"Sizning abonementingiz muddati yakunlandi ({sub.end_date.strftime('%d.%m.%Y')}).\n"
                    f"Yangi abonement xarid qilish uchun Telegram bot menyusidan foydalaning!"
                )
            )


def _send_unique_reminder(sub, msg_type, text):
    """Bir abonement davrida bir xil eslatmani takror yubormaslik"""
    client = sub.client
    if not client.telegram_user or not client.telegram_user.telegram_id:
        return

    tg_id = client.telegram_user.telegram_id

    # Avval shu xabar yuborilganmi tekshirish
    existing_notif = Notification.query.filter_by(
        client_id=client.id,
        telegram_id=tg_id,
        message_type=msg_type
    ).filter(Notification.created_at >= (datetime.now() - timedelta(days=2))).first()

    if existing_notif:
        return

    notif = Notification(
        client_id=client.id,
        telegram_id=tg_id,
        message_type=msg_type,
        message_text=text,
        status='pending'
    )
    db.session.add(notif)
    db.session.commit()

    # Yuborishga urinish
    success, _ = send_telegram_message(tg_id, text)
    if success:
        notif.status = 'sent'
        notif.sent_at = datetime.now()
    else:
        notif.status = 'failed'
    db.session.commit()


def run_auto_database_backup(app):
    """
    Avtomatik zaxira nusxa yaratish va audit qilish.
    """
    with app.app_context():
        try:
            from app.config import Config
            os.makedirs(Config.BACKUPS_FOLDER, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"iron_fitness_backup_{timestamp}.sql"
            backup_path = os.path.join(Config.BACKUPS_FOLDER, backup_filename)

            # Agar SQLite bo'lsa db faylini nusxalash
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            file_size = 0
            if 'sqlite' in db_uri:
                raw_path = db_uri.replace('sqlite:///', '')
                if os.path.exists(raw_path):
                    shutil.copy2(raw_path, backup_path)
                    file_size = os.path.getsize(backup_path)
            else:
                # MariaDB / MySQL mysqldump yoki export
                # Schema va seed nusxasini saqlash
                schema_path = os.path.join(os.path.dirname(Config.BASE_DIR), 'database', 'schema.sql')
                if os.path.exists(schema_path):
                    shutil.copy2(schema_path, backup_path)
                    file_size = os.path.getsize(backup_path)

            blog = BackupLog(
                file_name=backup_filename,
                file_size=file_size,
                backup_type='auto',
                status='success',
                message="Avtomatik zaxira nusxa muvaffaqiyatli yaratildi"
            )
            db.session.add(blog)
            db.session.commit()
        except Exception as e:
            blog = BackupLog(
                file_name="failed_backup",
                file_size=0,
                backup_type='auto',
                status='failed',
                message=str(e)
            )
            db.session.add(blog)
            db.session.commit()


def start_scheduler(app):
    """APScheduler vazifalarini ishga tushirish"""
    if not scheduler.running:
        # Har kuni soat 09:00 da eslatmalar
        scheduler.add_job(
            func=check_and_notify_expiring_subscriptions,
            trigger='interval',
            hours=6,
            args=[app],
            id='expiring_subs_check',
            replace_existing=True
        )

        # Har kuni soat 00:05 da muzlatish muddati o'tganlarni faollashtirish
        def unfreeze_job():
            with app.app_context():
                auto_unfreeze_expired_subscriptions()

        scheduler.add_job(
            func=unfreeze_job,
            trigger='interval',
            hours=1,
            id='auto_unfreeze_check',
            replace_existing=True
        )

        # Har kuni zaxira nusxa
        scheduler.add_job(
            func=run_auto_database_backup,
            trigger='interval',
            hours=24,
            args=[app],
            id='daily_backup_job',
            replace_existing=True
        )

        scheduler.start()
