from datetime import date, datetime, timedelta
from app.extensions import db
from app.models.subscription import Subscription, SubscriptionHistory, FreezeRequest
from app.models.client import Client
from app.models.setting import Setting, AuditLog
from app.models.notification import Notification

def create_freeze_request(client_id, days_count, reason=None, start_date=None):
    """
    Mijoz yoki bot orqali muzlatish so'rovini yaratish.
    Admin tasdig'isiz kuchga kirmaydi.
    """
    client = db.session.get(Client, client_id)
    if not client:
        return False, "Mijoz topilmadi"

    sub = client.active_subscription
    if not sub or sub.status != 'active':
        return False, "Mijozda ayni paytda faol abonement yo'q"

    # Sozlamalarni tekshirish
    max_days = int(Setting.get_value('max_freeze_days', '10'))
    max_per_period = int(Setting.get_value('max_freeze_per_period', '1'))

    if days_count > max_days:
        return False, f"Maksimal muzlatish muddati {max_days} kundan oshmasligi kerak"

    if sub.freeze_count >= max_per_period:
        return False, f"Ushbu abonement davrida muzlatish limiti ({max_per_period} marta) to'lgan"

    if start_date is None:
        start_date = date.today()
    elif isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    end_date = start_date + timedelta(days=days_count)

    # Kutilayotgan so'rov mavjudligini tekshirish
    pending_req = FreezeRequest.query.filter_by(
        subscription_id=sub.id,
        status='pending'
    ).first()
    if pending_req:
        return False, "Sizda allaqachon ko'rib chiqilayotgan muzlatish so'rovi mavjud"

    req = FreezeRequest(
        subscription_id=sub.id,
        client_id=client.id,
        start_date=start_date,
        end_date=end_date,
        days_count=days_count,
        reason=reason,
        status='pending'
    )
    db.session.add(req)
    db.session.commit()

    return True, req


def approve_freeze_request(freeze_req_id, admin_id, admin_comment=None):
    """
    Administrator tomonidan muzlatish so'rovini tasdiqlash.
    Abonement muddati muzlatilgan kunlar miqdoriga uzaytiriladi!
    """
    req = db.session.get(FreezeRequest, freeze_req_id)
    if not req or req.status != 'pending':
        return False, "So'rov topilmadi yoki allaqachon ko'rib chiqilgan"

    sub = req.subscription
    old_end_date = sub.end_date
    new_end_date = old_end_date + timedelta(days=req.days_count)

    req.status = 'approved'
    req.admin_comment = admin_comment
    req.reviewed_by = admin_id
    req.reviewed_at = datetime.now()

    sub.status = 'frozen'
    sub.freeze_count += 1
    sub.end_date = new_end_date

    # Tarixga yozish
    hist = SubscriptionHistory(
        subscription_id=sub.id,
        action='frozen',
        old_status='active',
        new_status='frozen',
        old_end_date=old_end_date,
        new_end_date=new_end_date,
        notes=f"Muzlatildi: {req.days_count} kun. Yangi tugash sanasi: {new_end_date.strftime('%d.%m.%Y')}. Izoh: {admin_comment or ''}",
        created_by='admin'
    )
    db.session.add(hist)

    # Audit
    AuditLog.log(
        action='FREEZE_APPROVED',
        admin_id=admin_id,
        table='freeze_requests',
        target_id=req.id,
        details=f"Mijoz: {req.client.full_name}, Kunlar: {req.days_count}, Yangi muddat: {new_end_date.strftime('%d.%m.%Y')}"
    )

    # Telegram orqali xabar yuborish navbatiga qo'shish
    if req.client.telegram_user:
        msg_text = (
            f"❄️ <b>Abonementingiz muzlatildi!</b>\n\n"
            f"📅 Boshlanish: {req.start_date.strftime('%d.%m.%Y')}\n"
            f"⏱ Davomiyligi: {req.days_count} kun\n"
            f"🏁 Yangi tugash sanasi: <b>{new_end_date.strftime('%d.%m.%Y')}</b>\n\n"
            f"Administrator izohi: {admin_comment or 'Tasdiqlandi'}"
        )
        notif = Notification(
            client_id=req.client.id,
            telegram_id=req.client.telegram_user.telegram_id,
            message_type='freeze_update',
            message_text=msg_text,
            status='pending'
        )
        db.session.add(notif)

    db.session.commit()
    return True, "Muzlatish so'rovi tasdiqlandi va abonement muddati uzaytirildi"


def reject_freeze_request(freeze_req_id, admin_id, admin_comment=None):
    """
    Administrator tomonidan so'rovni rad etish.
    """
    req = db.session.get(FreezeRequest, freeze_req_id)
    if not req or req.status != 'pending':
        return False, "So'rov topilmadi yoki allaqachon ko'rib chiqilgan"

    req.status = 'rejected'
    req.admin_comment = admin_comment
    req.reviewed_by = admin_id
    req.reviewed_at = datetime.now()

    AuditLog.log(
        action='FREEZE_REJECTED',
        admin_id=admin_id,
        table='freeze_requests',
        target_id=req.id,
        details=f"Mijoz: {req.client.full_name}, Sabab: {admin_comment or 'Sababsiz rad etildi'}"
    )

    if req.client.telegram_user:
        msg_text = (
            f"❌ <b>Muzlatish so'rovingiz rad etildi</b>\n\n"
            f"Sabab: {admin_comment or 'Klub qoidalariga mos kelmagani sababli'}"
        )
        notif = Notification(
            client_id=req.client.id,
            telegram_id=req.client.telegram_user.telegram_id,
            message_type='freeze_update',
            message_text=msg_text,
            status='pending'
        )
        db.session.add(notif)

    db.session.commit()
    return True, "So'rov rad etildi"


def auto_unfreeze_expired_subscriptions():
    """
    Muzlatish muddati yakunlangan abonementlarni avtomatik ravishda qayta faollashtirish.
    APScheduler orqali har kuni chaqiriladi.
    """
    today = date.today()
    frozen_subs = Subscription.query.filter_by(status='frozen').all()
    unfrozen_count = 0

    for sub in frozen_subs:
        # Eng so'nggi tasdiqlangan muzlatish so'rovini topish
        last_freeze = FreezeRequest.query.filter_by(
            subscription_id=sub.id,
            status='approved'
        ).order_by(FreezeRequest.id.desc()).first()

        if last_freeze and today >= last_freeze.end_date:
            sub.status = 'active'
            hist = SubscriptionHistory(
                subscription_id=sub.id,
                action='unfrozen',
                old_status='frozen',
                new_status='active',
                notes=f"Muzlatish davri ({last_freeze.end_date.strftime('%d.%m.%Y')}) tugadi va avtomatik faollashdi",
                created_by='system'
            )
            db.session.add(hist)

            if sub.client.telegram_user:
                notif = Notification(
                    client_id=sub.client.id,
                    telegram_id=sub.client.telegram_user.telegram_id,
                    message_type='freeze_update',
                    message_text=(
                        f"✅ <b>Abonementingiz qayta faollashdi!</b>\n\n"
                        f"Muzlatish davri tugadi. Sizni sport zalimizda kutib qolamiz!\n"
                        f"🏁 Joriy abonement tugash sanasi: <b>{sub.end_date.strftime('%d.%m.%Y')}</b>"
                    ),
                    status='pending'
                )
                db.session.add(notif)

            unfrozen_count += 1

    db.session.commit()
    return unfrozen_count
