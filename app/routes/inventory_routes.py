from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.product import Product, ProductCategory, Supplier, StockMovement
from app.models.setting import AuditLog
from app.forms.pos_forms import ProductForm, StockIncomeForm
from app.services.inventory_service import add_stock_income, write_off_stock, inventory_adjust_stock

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    low_stock = request.args.get('low_stock', '')

    query = Product.query.filter_by(is_active=True)

    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) |
            (Product.barcode.ilike(f"%{search}%"))
        )

    if category_id:
        query = query.filter_by(category_id=category_id)

    if low_stock == '1':
        query = query.filter(Product.stock_quantity <= Product.min_stock_alert)

    pagination = query.order_by(Product.name.asc()).paginate(page=page, per_page=15, error_out=False)
    products = pagination.items
    categories = ProductCategory.query.filter_by(is_active=True).all()

    return render_template(
        'inventory/index.html',
        products=products,
        pagination=pagination,
        categories=categories,
        search=search,
        selected_category_id=category_id,
        low_stock=low_stock
    )


@inventory_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = ProductForm()
    categories = ProductCategory.query.filter_by(is_active=True).all()
    suppliers = Supplier.query.filter_by(is_active=True).all()

    form.category_id.choices = [(0, 'Tanlanmagan')] + [(c.id, c.name) for c in categories]
    form.supplier_id.choices = [(0, 'Tanlanmagan')] + [(s.id, s.name) for s in suppliers]

    if form.validate_on_submit():
        clean_barcode = form.barcode.data.strip()
        existing = Product.query.filter_by(barcode=clean_barcode).first()
        if existing:
            flash("Ushbu shtrix-kodga ega mahsulot allaqachon mavjud!", "danger")
            return render_template('inventory/form.html', form=form, title="Yangi mahsulot qo'shish")

        cat_id = form.category_id.data if form.category_id.data > 0 else None
        sup_id = form.supplier_id.data if form.supplier_id.data > 0 else None

        prod = Product(
            name=form.name.data.strip(),
            barcode=clean_barcode,
            category_id=cat_id,
            supplier_id=sup_id,
            purchase_price=form.purchase_price.data,
            sale_price=form.sale_price.data,
            stock_quantity=form.stock_quantity.data,
            unit=form.unit.data,
            min_stock_alert=form.min_stock_alert.data,
            expiry_date=form.expiry_date.data,
            is_active=True
        )
        db.session.add(prod)
        db.session.flush()

        # Dastlabki kirim harakati
        if prod.stock_quantity > 0:
            m = StockMovement(
                product_id=prod.id,
                movement_type='in',
                quantity=prod.stock_quantity,
                previous_stock=0,
                new_stock=prod.stock_quantity,
                unit_price=prod.purchase_price,
                total_amount=float(prod.purchase_price) * prod.stock_quantity,
                notes="Boshlang'ich qoldiq",
                created_by=current_user.username
            )
            db.session.add(m)

        AuditLog.log(
            action='PRODUCT_CREATED',
            admin_id=current_user.id,
            table='products',
            target_id=prod.id,
            details=f"Yangi mahsulot {prod.name} (Barcode: {prod.barcode})"
        )

        db.session.commit()
        flash(f"Mahsulot '{prod.name}' muvaffaqiyatli saqlandi!", "success")
        return redirect(url_for('inventory.index'))

    return render_template('inventory/form.html', form=form, title="Yangi mahsulot qo'shish")


@inventory_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    prod = Product.query.get_or_404(id)
    form = ProductForm(obj=prod)
    categories = ProductCategory.query.filter_by(is_active=True).all()
    suppliers = Supplier.query.filter_by(is_active=True).all()

    form.category_id.choices = [(0, 'Tanlanmagan')] + [(c.id, c.name) for c in categories]
    form.supplier_id.choices = [(0, 'Tanlanmagan')] + [(s.id, s.name) for s in suppliers]

    if request.method == 'GET':
        form.category_id.data = prod.category_id or 0
        form.supplier_id.data = prod.supplier_id or 0

    if form.validate_on_submit():
        clean_barcode = form.barcode.data.strip()
        existing = Product.query.filter(Product.barcode == clean_barcode, Product.id != prod.id).first()
        if existing:
            flash("Ushbu shtrix-kod boshqa mahsulotga biriktirilgan!", "danger")
            return render_template('inventory/form.html', form=form, title="Mahsulotni tahrirlash", product=prod)

        prod.name = form.name.data.strip()
        prod.barcode = clean_barcode
        prod.category_id = form.category_id.data if form.category_id.data > 0 else None
        prod.supplier_id = form.supplier_id.data if form.supplier_id.data > 0 else None
        prod.purchase_price = form.purchase_price.data
        prod.sale_price = form.sale_price.data
        prod.unit = form.unit.data
        prod.min_stock_alert = form.min_stock_alert.data
        prod.expiry_date = form.expiry_date.data

        AuditLog.log(
            action='PRODUCT_UPDATED',
            admin_id=current_user.id,
            table='products',
            target_id=prod.id,
            details=f"Mahsulot {prod.name} tahrirlandi"
        )

        db.session.commit()
        flash(f"Mahsulot '{prod.name}' ma'lumotlari yangilandi!", "success")
        return redirect(url_for('inventory.index'))

    return render_template('inventory/form.html', form=form, title="Mahsulotni tahrirlash", product=prod)


@inventory_bp.route('/income', methods=['GET', 'POST'])
@login_required
def income():
    """Omborga partiya kirimi qilish"""
    products = Product.query.filter_by(is_active=True).order_by(Product.name.asc()).all()

    if request.method == 'POST':
        product_id = request.form.get('product_id', type=int)
        quantity = request.form.get('quantity', type=int)
        purchase_price = request.form.get('purchase_price', type=float)
        notes = request.form.get('notes', '').strip()

        success, msg = add_stock_income(
            product_id=product_id,
            quantity=quantity,
            purchase_price=purchase_price,
            notes=notes,
            admin_username=current_user.username
        )
        if success:
            flash(msg, "success")
            return redirect(url_for('inventory.index'))
        else:
            flash(msg, "danger")

    return render_template('inventory/income.html', products=products)


@inventory_bp.route('/write_off', methods=['POST'])
@login_required
def write_off():
    """Yaroqsiz mahsulotni hisobdan chiqarish"""
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int)
    reason = request.form.get('reason', "Yaroqsiz").strip()

    success, msg = write_off_stock(product_id, quantity, reason, current_user.username)
    if success:
        flash(msg, "warning")
    else:
        flash(msg, "danger")
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/adjust', methods=['POST'])
@login_required
def adjust():
    """Inventarizatsiya qoldig'ini to'g'rilash"""
    product_id = request.form.get('product_id', type=int)
    actual_quantity = request.form.get('actual_quantity', type=int)
    reason = request.form.get('reason', 'Inventarizatsiya').strip()

    success, msg = inventory_adjust_stock(product_id, actual_quantity, reason, current_user.username)
    if success:
        flash(msg, "info")
    else:
        flash(msg, "danger")
    return redirect(url_for('inventory.index'))


@inventory_bp.route('/movements')
@login_required
def movements():
    """Ombor harakatlari tarixi"""
    page = request.args.get('page', 1, type=int)
    movements_list = StockMovement.query.order_by(StockMovement.id.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('inventory/movements.html', movements=movements_list.items, pagination=movements_list)
