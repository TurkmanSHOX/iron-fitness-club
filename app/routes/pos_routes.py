from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from app.extensions import db
from app.models.product import Product, ProductCategory
from app.models.sale import Sale
from app.models.client import Client
from app.services.pos_service import find_product_by_barcode, process_pos_checkout, refund_or_cancel_sale

pos_bp = Blueprint('pos', __name__)

@pos_bp.route('/')
@login_required
def index():
    """Kassa va mahsulotlar savdosi (POS) asosiy oynasi"""
    categories = ProductCategory.query.filter_by(is_active=True).all()
    products = Product.query.filter_by(is_active=True).all()
    clients = Client.query.filter_by(status='active').order_by(Client.full_name.asc()).all()

    return render_template(
        'pos/index.html',
        categories=categories,
        products=products,
        clients=clients
    )


@pos_bp.route('/api/search_barcode')
@login_required
def search_barcode():
    """2D skaner orqali shtrix-kodni qidirish"""
    barcode = request.args.get('barcode', '').strip()
    product = find_product_by_barcode(barcode)
    if not product:
        return jsonify({'success': False, 'message': 'Mahsulot topilmadi'}), 404

    return jsonify({
        'success': True,
        'product': {
            'id': product.id,
            'name': product.name,
            'barcode': product.barcode,
            'sale_price': float(product.sale_price),
            'stock_quantity': product.stock_quantity,
            'unit': product.unit
        }
    })


@pos_bp.route('/api/checkout', methods=['POST'])
@login_required
def checkout_api():
    """Savatdagi mahsulotlarni kassa orqali sotish"""
    data = request.get_json() or {}
    items = data.get('items', [])
    payment_method = data.get('payment_method', 'cash')
    client_id = data.get('client_id')
    discount_amount = float(data.get('discount_amount', 0))
    notes = data.get('notes')

    if client_id:
        try:
            client_id = int(client_id)
        except Exception:
            client_id = None

    success, result = process_pos_checkout(
        items_data=items,
        payment_method=payment_method,
        client_id=client_id,
        discount_amount=discount_amount,
        notes=notes,
        created_by=current_user.username
    )

    if not success:
        return jsonify({'success': False, 'message': result}), 400

    sale = result
    return jsonify({
        'success': True,
        'sale_id': sale.id,
        'sale_number': sale.sale_number,
        'final_amount': float(sale.final_amount),
        'receipt_url': url_for('pos.download_receipt', id=sale.id),
        'message': f"Savdo №{sale.sale_number} muvaffaqiyatli yakunlandi!"
    })


@pos_bp.route('/sales')
@login_required
def sales_history():
    """Barcha savdolar tarixi"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()

    query = Sale.query
    if search:
        query = query.filter(Sale.sale_number.ilike(f"%{search}%"))

    pagination = query.order_by(Sale.id.desc()).paginate(page=page, per_page=15, error_out=False)
    sales = pagination.items

    return render_template(
        'pos/sales.html',
        sales=sales,
        pagination=pagination,
        search=search
    )


@pos_bp.route('/sales/<int:id>/receipt')
@login_required
def download_receipt(id):
    """Savdo chekini yuklab olish yoki ko'rish"""
    sale = Sale.query.get_or_404(id)
    if not sale.receipt_pdf_path:
        flash("Ushbu savdo uchun PDF chek mavjud emas", "warning")
        return redirect(url_for('pos.sales_history'))

    from app.config import Config
    import os
    full_path = os.path.join(Config.BASE_DIR, 'uploads', sale.receipt_pdf_path)
    if not os.path.exists(full_path):
        flash("Chek fayli topilmadi", "danger")
        return redirect(url_for('pos.sales_history'))

    return send_file(full_path, mimetype='application/pdf')


@pos_bp.route('/sales/<int:id>/refund', methods=['POST'])
@login_required
def refund_sale(id):
    """Savdoni qaytarish va ombor qoldig'ini tiklash"""
    reason = request.form.get('reason', 'Mijoz tovar qaytardi').strip()
    success, msg = refund_or_cancel_sale(id, reason, current_user.username)
    if success:
        flash(msg, "success")
    else:
        flash(msg, "danger")
    return redirect(url_for('pos.sales_history'))
