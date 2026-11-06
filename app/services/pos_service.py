import os
from datetime import datetime
from app.extensions import db
from app.models.product import Product, StockMovement
from app.models.sale import Sale, SaleItem
from app.models.payment import Payment
from app.models.client import Client
from app.models.setting import Setting, AuditLog
from app.services.pdf_service import generate_receipt_pdf

def find_product_by_barcode(barcode):
    """2D skaner orqali o'qilgan shtrix-kod bo'yicha mahsulotni topish"""
    clean_code = str(barcode).strip()
    return Product.query.filter_by(barcode=clean_code, is_active=True).first()


def process_pos_checkout(items_data, payment_method='cash', client_id=None, 
                         discount_amount=0, notes=None, created_by='admin'):
    """
    Kassa savdosini tranzaksiya orqali atomik amalga oshirish.
    items_data: [{'product_id': 1, 'quantity': 2}, ...]
    """
    if not items_data:
        return False, "Savat bo'sh! Kamida bitta mahsulot qo'shing."

    # Tranzaksiya ichida qoldiqni tekshirish
    validated_items = []
    total_amount = 0.0
    total_cost = 0.0

    for item in items_data:
        p_id = int(item['product_id'])
        qty = int(item['quantity'])
        if qty <= 0:
            continue

        product = db.session.get(Product, p_id, with_for_update=True)
        if not product or not product.is_active:
            return False, f"Mahsulot topilmadi yoki nofaol (ID: {p_id})"

        if product.stock_quantity < qty:
            return False, f"'{product.name}' mahsulotidan yetarli qoldiq yo'q! Omborda: {product.stock_quantity} {product.unit}, so'ralgan: {qty} {product.unit}"

        item_total = float(product.sale_price) * qty
        item_cost = float(product.purchase_price) * qty
        total_amount += item_total
        total_cost += item_cost

        validated_items.append({
            'product': product,
            'qty': qty,
            'unit_price': product.sale_price,
            'purchase_price': product.purchase_price,
            'total_price': item_total
        })

    if not validated_items:
        return False, "Savatda yaroqli mahsulotlar yo'q."

    discount = float(discount_amount)
    final_amount = max(0.0, total_amount - discount)
    gross_profit = final_amount - total_cost

    # Savdo yozuvi
    sale_number = f"SALE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{int(datetime.now().timestamp()) % 1000}"
    sale = Sale(
        sale_number=sale_number,
        client_id=client_id if client_id else None,
        total_amount=total_amount,
        discount_amount=discount,
        final_amount=final_amount,
        cost_amount=total_cost,
        gross_profit=gross_profit,
        payment_method=payment_method,
        status='completed',
        notes=notes,
        created_by=created_by
    )
    db.session.add(sale)
    db.session.flush()

    # Mahsulotlarni kamaytirish va harakatlarini saqlash
    receipt_items = []
    for v_item in validated_items:
        prod = v_item['product']
        qty = v_item['qty']
        prev_stock = prod.stock_quantity
        new_stock = prev_stock - qty

        prod.stock_quantity = new_stock

        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=prod.id,
            product_name=prod.name,
            barcode=prod.barcode,
            purchase_price=v_item['purchase_price'],
            unit_price=v_item['unit_price'],
            quantity=qty,
            total_price=v_item['total_price']
        )
        db.session.add(sale_item)

        movement = StockMovement(
            product_id=prod.id,
            movement_type='out_sale',
            quantity=qty,
            previous_stock=prev_stock,
            new_stock=new_stock,
            unit_price=v_item['unit_price'],
            total_amount=v_item['total_price'],
            reference_id=sale.sale_number,
            notes=f"Kassa savdosi №{sale.sale_number}",
            created_by=created_by
        )
        db.session.add(movement)

        receipt_items.append({
            'name': prod.name,
            'qty': qty,
            'price': prod.sale_price,
            'total': v_item['total_price']
        })

    # To'lov yozuvi
    payment = Payment(
        payment_number=f"PAY-{sale.sale_number}",
        client_id=client_id if client_id else 1,  # Agar noma'lum mijoz bo'lsa default 1 yoki anonim
        sale_id=sale.id,
        payment_type='product_sale',
        amount=final_amount,
        payment_method=payment_method,
        status='completed',
        created_by=created_by
    )
    db.session.add(payment)

    AuditLog.log(
        action='POS_SALE_COMPLETED',
        admin_id=None,
        table='sales',
        target_id=sale.id,
        details=f"Savdo №{sale.sale_number}, Summa: {final_amount} so'm, To'lov: {payment_method}"
    )

    db.session.commit()

    # Elektron PDF chek
    try:
        from app.config import Config
        client_name = "Umumiy mijoz (Kassa)"
        if client_id:
            c = Client.query.get(client_id)
            if c:
                client_name = c.full_name

        receipt_filename = f"receipt_{sale.sale_number}.pdf"
        receipt_path = os.path.join(Config.RECEIPTS_FOLDER, receipt_filename)
        receipt_data = {
            'receipt_number': sale.sale_number,
            'club_name': Setting.get_value('club_name', 'IRON FITNESS CLUB'),
            'club_phone': Setting.get_value('club_phone', '+998 90 123 45 67'),
            'club_address': Setting.get_value('club_address', 'Urganch shahri'),
            'date_time': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'client_name': client_name,
            'items': receipt_items,
            'subtotal': total_amount,
            'discount': discount,
            'total': final_amount,
            'payment_method': payment.method_label,
            'qr_token': sale.sale_number
        }
        generate_receipt_pdf(receipt_data, receipt_path)
        sale.receipt_pdf_path = f"receipts/{receipt_filename}"
        payment.receipt_pdf_path = f"receipts/{receipt_filename}"
        db.session.commit()
    except Exception as e:
        print(f"POS PDF chek ogohlantirish: {e}")

    return True, sale


def refund_or_cancel_sale(sale_id, reason="Admin bekor qildi", admin_username='admin'):
    """
    Savdoni bekor qilish yoki qaytarish:
    Ombor qoldig'i tiklanadi, harakatga 'return' yoziladi, holat 'refunded' qilinadi.
    """
    sale = db.session.get(Sale, sale_id)
    if not sale or sale.status in ['cancelled', 'refunded']:
        return False, "Savdo topilmadi yoki allaqachon bekor qilingan"

    # Har bir mahsulotni omborga qaytarish
    for item in sale.items:
        prod = db.session.get(Product, item.product_id)
        if prod:
            prev_stock = prod.stock_quantity
            new_stock = prev_stock + item.quantity
            prod.stock_quantity = new_stock

            movement = StockMovement(
                product_id=prod.id,
                movement_type='return',
                quantity=item.quantity,
                previous_stock=prev_stock,
                new_stock=new_stock,
                unit_price=item.unit_price,
                total_amount=item.total_price,
                reference_id=sale.sale_number,
                notes=f"Qaytarish: Savdo №{sale.sale_number}. Sabab: {reason}",
                created_by=admin_username
            )
            db.session.add(movement)

    sale.status = 'refunded'
    sale.notes = f"{sale.notes or ''}\n[Qaytarildi: {reason}]"

    # To'lovni ham bekor qilish
    for p in sale.payments:
        p.status = 'refunded'

    AuditLog.log(
        action='POS_SALE_REFUNDED',
        admin_id=None,
        table='sales',
        target_id=sale.id,
        details=f"Savdo №{sale.sale_number} qaytarildi. Sabab: {reason}"
    )

    db.session.commit()
    return True, f"Savdo №{sale.sale_number} muvaffaqiyatli qaytarildi va mahsulotlar omborga tiklandi"
