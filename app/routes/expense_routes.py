import os
from datetime import date, datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.config import Config
from app.models.expense import Expense
from app.models.setting import AuditLog
from app.forms.pos_forms import ExpenseForm

expense_bp = Blueprint('expenses', __name__)

@expense_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', 'all')
    month_filter = request.args.get('month', '')

    query = Expense.query

    if category_filter != 'all':
        query = query.filter_by(category=category_filter)

    if month_filter:
        try:
            m_date = datetime.strptime(month_filter, '%Y-%m').date()
            query = query.filter(
                db.extract('year', Expense.expense_date) == m_date.year,
                db.extract('month', Expense.expense_date) == m_date.month
            )
        except Exception:
            pass

    pagination = query.order_by(Expense.expense_date.desc(), Expense.id.desc()).paginate(page=page, per_page=15, error_out=False)
    expenses = pagination.items

    total_expense = sum(float(e.amount) for e in query.all())

    return render_template(
        'expenses/index.html',
        expenses=expenses,
        pagination=pagination,
        category_filter=category_filter,
        month_filter=month_filter,
        total_expense=total_expense
    )


@expense_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = ExpenseForm()
    if request.method == 'GET' and not form.expense_date.data:
        form.expense_date.data = date.today()

    if form.validate_on_submit():
        receipt_filename = None
        if form.receipt_image.data:
            f = form.receipt_image.data
            ext = f.filename.rsplit('.', 1)[1].lower()
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            receipt_filename = f"expense_{timestamp}.{ext}"
            os.makedirs(os.path.join(Config.UPLOAD_FOLDER, 'expenses'), exist_ok=True)
            f.save(os.path.join(Config.UPLOAD_FOLDER, 'expenses', receipt_filename))

        expense = Expense(
            title=form.title.data.strip(),
            category=form.category.data,
            amount=form.amount.data,
            payment_method=form.payment_method.data,
            expense_date=form.expense_date.data,
            receipt_image=f"expenses/{receipt_filename}" if receipt_filename else None,
            notes=form.notes.data,
            created_by=current_user.username
        )
        db.session.add(expense)
        db.session.flush()

        AuditLog.log(
            action='EXPENSE_CREATED',
            admin_id=current_user.id,
            table='expenses',
            target_id=expense.id,
            details=f"Xarajat '{expense.title}' ({expense.amount} UZS, Kategoriya: {expense.category})"
        )

        db.session.commit()
        flash(f"Xarajat '{expense.title}' muvaffaqiyatli saqlandi!", "success")
        return redirect(url_for('expenses.index'))

    return render_template('expenses/form.html', form=form, title="Yangi xarajat qo'shish")


@expense_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    expense = Expense.query.get_or_404(id)
    title = expense.title
    db.session.delete(expense)

    AuditLog.log(
        action='EXPENSE_DELETED',
        admin_id=current_user.id,
        table='expenses',
        target_id=id,
        details=f"Xarajat '{title}' o'chirildi"
    )

    db.session.commit()
    flash(f"Xarajat '{title}' o'chirildi", "info")
    return redirect(url_for('expenses.index'))
