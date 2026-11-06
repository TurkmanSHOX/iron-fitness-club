from datetime import date, timedelta
from app.extensions import db
from app.models.product import Product, StockMovement, ProductCategory, Supplier
from app.models.setting import AuditLog

def add_stock_income(product_id, quantity, purchase_price=None, supplier_id=None, notes=None, admin_username='admin'):
    """
    Omborga mahsulot kirimi (partiya xaridi).
    """
    product = Product.query.get(product_id)
    if not product:
        return False, "Mahsulot topilmadi"

    qty = int(quantity)
    if qty <= 0:
        return False, "Kirim miqdori musbat son bo'lishi kerak"

    prev_stock = product.stock_quantity
    new_stock = prev_stock + qty
    product.stock_quantity = new_stock

    if purchase_price is not None and float(purchase_price) > 0:
        product.purchase_price = float(purchase_price)

    if supplier_id:
        product.supplier_id = supplier_id

    unit_price = product.purchase_price
    total_amount = float(unit_price) * qty

    movement = StockMovement(
        product_id=product.id,
        movement_type='in',
        quantity=qty,
        previous_stock=prev_stock,
        new_stock=new_stock,
        unit_price=unit_price,
        total_amount=total_amount,
        notes=notes or "Omborga kirim",
        created_by=admin_username
    )
    db.session.add(movement)

    AuditLog.log(
        action='STOCK_INCOME',
        admin_id=None,
        table='products',
        target_id=product.id,
        details=f"{product.name}: +{qty} {product.unit} (Yangi qoldiq: {new_stock})"
    )

    db.session.commit()
    return True, f"'{product.name}' omboriga {qty} {product.unit} muvaffaqiyatli kirim qilindi"


def write_off_stock(product_id, quantity, reason="Muddati o'tgan yoki yaroqsiz", admin_username='admin'):
    """
    Yaroqsiz mahsulotni hisobdan chiqarish (Spisanie).
    """
    product = Product.query.get(product_id)
    if not product:
        return False, "Mahsulot topilmadi"

    qty = int(quantity)
    if qty <= 0:
        return False, "Chiqarish miqdori musbat son bo'lishi kerak"

    if product.stock_quantity < qty:
        return False, f"Omborda bunday miqdorda qoldiq yo'q (Mavjud: {product.stock_quantity})"

    prev_stock = product.stock_quantity
    new_stock = prev_stock - qty
    product.stock_quantity = new_stock

    movement = StockMovement(
        product_id=product.id,
        movement_type='write_off',
        quantity=qty,
        previous_stock=prev_stock,
        new_stock=new_stock,
        unit_price=product.purchase_price,
        total_amount=float(product.purchase_price) * qty,
        notes=f"Hisobdan chiqarish: {reason}",
        created_by=admin_username
    )
    db.session.add(movement)

    AuditLog.log(
        action='STOCK_WRITE_OFF',
        admin_id=None,
        table='products',
        target_id=product.id,
        details=f"{product.name}: -{qty} {product.unit}. Sabab: {reason}"
    )

    db.session.commit()
    return True, f"'{product.name}' dan {qty} {product.unit} hisobdan chiqarildi"


def inventory_adjust_stock(product_id, actual_quantity, reason="Inventarizatsiya natijasi", admin_username='admin'):
    """
    Inventarizatsiya natijasida faktik qoldiqni to'g'rilash.
    """
    product = Product.query.get(product_id)
    if not product:
        return False, "Mahsulot topilmadi"

    actual_qty = int(actual_quantity)
    if actual_qty < 0:
        return False, "Qoldiq manfiy bo'lishi mumkin emas"

    prev_stock = product.stock_quantity
    diff = actual_qty - prev_stock
    product.stock_quantity = actual_qty

    movement = StockMovement(
        product_id=product.id,
        movement_type='inventory_adjustment',
        quantity=abs(diff),
        previous_stock=prev_stock,
        new_stock=actual_qty,
        unit_price=product.sale_price,
        total_amount=float(product.sale_price) * abs(diff),
        notes=f"Inventarizatsiya tuzatishi: {prev_stock} -> {actual_qty}. Sabab: {reason}",
        created_by=admin_username
    )
    db.session.add(movement)

    AuditLog.log(
        action='INVENTORY_ADJUST',
        admin_id=None,
        table='products',
        target_id=product.id,
        details=f"{product.name} qoldig'i {prev_stock} dan {actual_qty} ga o'zgartirildi"
    )

    db.session.commit()
    return True, f"'{product.name}' qoldig'i muvaffaqiyatli {actual_qty} {product.unit} deb belgilandi"


def get_low_stock_products():
    """Minimal qoldiqdan kamaygan barcha mahsulotlar ro'yxati"""
    return Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity <= Product.min_stock_alert
    ).order_by(Product.stock_quantity.asc()).all()


def get_expiring_products(days_threshold=30):
    """Yaroqlilik muddati yaqinlashayotgan mahsulotlar"""
    limit_date = date.today() + timedelta(days=days_threshold)
    return Product.query.filter(
        Product.is_active == True,
        Product.expiry_date != None,
        Product.expiry_date <= limit_date
    ).order_by(Product.expiry_date.asc()).all()
