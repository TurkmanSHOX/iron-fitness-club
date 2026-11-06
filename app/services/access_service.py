from datetime import date, datetime
from app.extensions import db
from app.models.client import Client, ClientQRCode
from app.models.subscription import Subscription
from app.models.visit import Visit, AccessAttempt
from app.models.setting import Setting, AuditLog

def check_in_client(qr_token_or_client_id, scan_type='qr', admin_id=None, override_reason=None):
    """
    Texnik topshiriqning 8-bo'limiga muvofiq kirishni tekshirish va qayd etish.
    
    Qoidalar:
    1. Mijoz mavjudligi va holati
    2. Faol abonement mavjudligi
    3. Abonement to'langanligi va muddati
    4. Bugungi sana tarifga mosligi (toq / juft / har kuni)
    5. Abonement muzlatilmaganligi
    6. Bir kunda faqat 1 marta kirish qoidasi
    7. Administrator istisno tariqasida kiritish imkoniyati
    """
    today = date.today()
    now_time = datetime.now().time()
    
    # 1. Mijozni aniqlash
    client = None
    if isinstance(qr_token_or_client_id, int) or (isinstance(qr_token_or_client_id, str) and qr_token_or_client_id.isdigit()):
        client = Client.query.get(int(qr_token_or_client_id))
    else:
        # QR token orqali qidirish
        token = str(qr_token_or_client_id).strip()
        client = Client.query.filter_by(qr_code=token).first()
        if not client:
            qr_rec = ClientQRCode.query.filter_by(qr_code_token=token, is_active=True).first()
            if qr_rec:
                client = qr_rec.client

    if not client:
        AccessAttempt.query.session.add(AccessAttempt(
            client_id=None,
            qr_code=str(qr_token_or_client_id),
            status='denied',
            reason="QR-kod tizimda ro'yxatdan o'tmagan"
        ))
        db.session.commit()
        return {
            'success': False,
            'status': 'denied',
            'client': None,
            'reason': "QR-kod tizimda ro'yxatdan o'tmagan. Mijoz topilmadi.",
            'color': 'danger'
        }

    # 2. Mijoz holatini tekshirish
    if client.status != 'active':
        reason = f"Mijoz hisobi nofaol (Holati: {client.status})"
        _record_denial(client, str(qr_token_or_client_id), reason)
        return {
            'success': False,
            'status': 'denied',
            'client': client,
            'reason': reason,
            'color': 'danger'
        }

    # 3. Faol abonementni tekshirish
    sub = client.active_subscription
    if not sub:
        reason = "Mijozda faol abonement mavjud emas"
        return _handle_denial_or_override(client, None, str(qr_token_or_client_id), reason, scan_type, admin_id, override_reason)

    # 4. Muzlatilganligini tekshirish
    if sub.status == 'frozen':
        reason = "Abonement ayni paytda MUZLATILGAN holatda"
        return _handle_denial_or_override(client, sub, str(qr_token_or_client_id), reason, scan_type, admin_id, override_reason)

    # 5. Muddatini tekshirish
    if today < sub.start_date:
        reason = f"Abonement {sub.start_date.strftime('%d.%m.%Y')} sanasidan boshlanadi"
        return _handle_denial_or_override(client, sub, str(qr_token_or_client_id), reason, scan_type, admin_id, override_reason)

    if today > sub.end_date:
        sub.status = 'expired'
        db.session.commit()
        reason = f"Abonement muddati {sub.end_date.strftime('%d.%m.%Y')} sanasida tugagan"
        return _handle_denial_or_override(client, sub, str(qr_token_or_client_id), reason, scan_type, admin_id, override_reason)

    # 6. Tarif sanasi (juft / toq) tekshiruvi
    day_allowed, day_msg = sub.is_day_allowed(today)
    if not day_allowed:
        return _handle_denial_or_override(client, sub, str(qr_token_or_client_id), day_msg, scan_type, admin_id, override_reason)

    # 7. Bir kunda 1 marta kirish qoidasi
    single_entry_setting = Setting.get_value('single_entry_per_day', 'true').lower() == 'true'
    if single_entry_setting:
        existing_today = Visit.query.filter(
            Visit.client_id == client.id,
            Visit.visit_date == today,
            Visit.status == 'allowed'
        ).first()

        if existing_today:
            reason = f"Mijoz bugun allaqachon kirgan ({existing_today.visit_time.strftime('%H:%M')}). Takroriy kirish taqiqlangan!"
            return _handle_denial_or_override(client, sub, str(qr_token_or_client_id), reason, scan_type, admin_id, override_reason)

    # BARCHA SHARTLAR BAJARILDI: MUVAFFAQIYATLI RUXSAT!
    visit = Visit(
        client_id=client.id,
        subscription_id=sub.id,
        visit_date=today,
        visit_time=now_time,
        scan_type=scan_type,
        status='allowed',
        notes="QR orqali muvaffaqiyatli kirish" if scan_type == 'qr' else "Qo'lda kiritildi",
        admin_id=admin_id
    )
    db.session.add(visit)

    # 1 kunlik tashrif bo'lsa, foydalanilgan deb muddati tugatiladi
    if sub.tariff.type == 'single':
        sub.status = 'expired'

    # Audit log
    db.session.add(AccessAttempt(
        client_id=client.id,
        qr_code=str(qr_token_or_client_id),
        status='allowed',
        reason="Muvaffaqiyatli ruxsat"
    ))
    db.session.commit()

    return {
        'success': True,
        'status': 'allowed',
        'client': client,
        'subscription': sub,
        'visit': visit,
        'reason': "Kirishga ruxsat berildi! Xush kelibsiz!",
        'color': 'success'
    }


def _handle_denial_or_override(client, sub, qr_token, reason, scan_type, admin_id, override_reason):
    """
    Agar rad etilgan bo'lsa, ammo administrator sabab ko'rsatib istisno ruxsat bersa
    """
    today = date.today()
    now_time = datetime.now().time()

    if override_reason and admin_id:
        # Administrator istisno tariqasida ruxsat berdi
        visit = Visit(
            client_id=client.id,
            subscription_id=sub.id if sub else None,
            visit_date=today,
            visit_time=now_time,
            scan_type='manual',
            status='allowed',
            notes=f"ADMIN ISTISNO RUXSATI: {override_reason} (Asl sabab: {reason})",
            admin_id=admin_id
        )
        db.session.add(visit)

        AuditLog.log(
            action='ACCESS_OVERRIDE',
            admin_id=admin_id,
            table='visits',
            target_id=client.id,
            details=f"Mijoz: {client.full_name}, Sabab: {override_reason}, Qoidabuzarlik: {reason}"
        )
        db.session.commit()

        return {
            'success': True,
            'status': 'allowed',
            'client': client,
            'subscription': sub,
            'visit': visit,
            'reason': f"Admin istisno tariqasida ruxsat berdi: {override_reason}",
            'color': 'warning'
        }

    # Oddiy rad etish
    _record_denial(client, qr_token, reason)
    return {
        'success': False,
        'status': 'denied',
        'client': client,
        'subscription': sub,
        'reason': reason,
        'color': 'danger'
    }


def _record_denial(client, qr_token, reason):
    """Rad etilgan urinishni jurnalga saqlash"""
    attempt = AccessAttempt(
        client_id=client.id if client else None,
        qr_code=qr_token,
        status='denied',
        reason=reason
    )
    db.session.add(attempt)
    db.session.commit()
