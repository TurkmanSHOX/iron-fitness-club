import os
import calendar
from datetime import date, datetime, timedelta
from app.extensions import db
from app.models.subscription import Subscription, SubscriptionHistory
from app.models.tariff import Tariff
from app.models.client import Client
from app.models.payment import Payment
from app.models.setting import Setting, AuditLog
from app.services.pdf_service import generate_receipt_pdf

def calculate_subscription_end_date(start_date, duration_days=30):
    """
    Texnik topshiriqning 7.3 bandiga muvofiq kalendar oy bo'yicha hisoblash.
    Masalan: 31-yanvarda boshlansa, fevral oyining oxirgi kalendar kuni (28 yoki 29) bo'ladi.
    Agar 1 kunlik bo'lsa, start_date bilan bir xil bo'ladi.
    """
    if duration_days == 1:
        return start_date

    if 28 <= duration_days <= 31:
        year = start_date.year
        month = start_date.month

        # Keyingi oyni hisoblash
        if month == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month + 1

        _, max_days_in_next_month = calendar.monthrange(next_year, next_month)
        next_day = min(start_date.day, max_days_in_next_month)
        return date(next_year, next_month, next_day)

    return start_date + timedelta(days=duration_days)


def create_subscription(client_id, tariff_id, payment_method='cash', paid_amount=None, 
                        start_date=None, discount_amount=0, notes=None, created_by='admin'):
    """
    Yangi abonement yaratadi, to'lovni qayd etadi va tarixga yozadi.
    """
    client = db.session.get(Client, client_id)
    tariff = db.session.get(Tariff, tariff_id)

    if not client:
        raise ValueError("Mijoz topilmadi")
    if not tariff:
        raise ValueError("Tarif topilmadi")

    if start_date is None:
        start_date = date.today()
    elif isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

    end_date = calculate_subscription_end_date(start_date, tariff.duration_days)

    final_price = float(tariff.price) - float(discount_amount)
    if final_price < 0:
        final_price = 0

    if paid_amount is None:
        paid_amount = final_price

    # Agar mijozda ayni paytda faol abonement bo'lsa, uni eskirgan deb belgilaymiz yoki uzaytiramiz
    existing_sub = client.active_subscription
    if existing_sub and existing_sub.status == 'active':
        # Agar yangi abonement joriy abonement tugagandan keyin boshlansa:
        if existing_sub.end_date >= start_date:
            start_date = existing_sub.end_date + timedelta(days=1)
            end_date = calculate_subscription_end_date(start_date, tariff.duration_days)

    # 1. Abonement yozuvi
    sub = Subscription(
        client_id=client.id,
        tariff_id=tariff.id,
        start_date=start_date,
        end_date=end_date,
        original_price=tariff.price,  # Tarif narxi kelajakda o'zgarsa ham, xarid narxi saqlanadi
        paid_amount=paid_amount,
        status='active',
        notes=notes
    )
    db.session.add(sub)
    db.session.flush()

    # 2. To'lov yozuvi
    pay_number = f"PAY-{datetime.now().strftime('%Y%m%d%H%M%S')}-{sub.id}"
    payment = Payment(
        payment_number=pay_number,
        client_id=client.id,
        subscription_id=sub.id,
        payment_type='single_visit' if tariff.type == 'single' else 'subscription',
        amount=paid_amount,
        payment_method=payment_method,
        status='completed',
        created_by=created_by
    )
    db.session.add(payment)

    # 3. Tarix yozuvi
    sub_hist = SubscriptionHistory(
        subscription_id=sub.id,
        action='created',
        old_status=None,
        new_status='active',
        old_end_date=None,
        new_end_date=end_date,
        notes=f"Tarif: {tariff.name}, To'lov: {payment_method}",
        created_by=created_by
    )
    db.session.add(sub_hist)

    # 4. Audit
    AuditLog.log(
        action='SUBSCRIPTION_CREATED',
        admin_id=None,
        table='subscriptions',
        target_id=sub.id,
        details=f"Client: {client.full_name}, Tariff: {tariff.name}, Summa: {paid_amount} UZS"
    )

    db.session.commit()

    # 5. Elektron PDF chek yaratish
    try:
        from app.config import Config
        receipt_filename = f"receipt_{payment.payment_number}.pdf"
        receipt_path = os.path.join(Config.RECEIPTS_FOLDER, receipt_filename)
        receipt_data = {
            'receipt_number': payment.payment_number,
            'club_name': Setting.get_value('club_name', 'IRON FITNESS CLUB'),
            'club_phone': Setting.get_value('club_phone', '+998 90 123 45 67'),
            'club_address': Setting.get_value('club_address', 'Urganch shahri'),
            'date_time': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'client_name': client.full_name,
            'items': [{
                'name': tariff.name,
                'qty': 1,
                'price': tariff.price,
                'total': paid_amount
            }],
            'subtotal': tariff.price,
            'discount': discount_amount,
            'total': paid_amount,
            'payment_method': payment.method_label,
            'qr_token': client.qr_code
        }
        generate_receipt_pdf(receipt_data, receipt_path)
        payment.receipt_pdf_path = f"receipts/{receipt_filename}"
        db.session.commit()
    except Exception as e:
        print(f"PDF chek yaratishda ogohlantirish: {e}")

    return sub
