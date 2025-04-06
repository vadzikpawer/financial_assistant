from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from models import Transaction, BankAccount, Category
from sqlalchemy import desc
from datetime import datetime, timedelta
import pandas as pd
from services.transaction_analyzer import analyze_transactions, categorize_transaction

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/transactions')
@login_required
def transactions():
    # Get filter parameters
    account_id = request.args.get('account_id', type=int)
    category_id = request.args.get('category_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Base query - get transactions from user's accounts
    query = (Transaction.query
             .join(BankAccount)
             .filter(BankAccount.user_id == current_user.id))
    
    # Apply filters
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    
    if category_id:
        query = query.filter(Transaction.category_id == category_id)
    
    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(Transaction.transaction_date >= date_from)
    
    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
        # Add one day to include the end date
        date_to = date_to + timedelta(days=1)
        query = query.filter(Transaction.transaction_date < date_to)
    
    # Get sorted transactions
    transactions = query.order_by(desc(Transaction.transaction_date)).all()
    
    # Get user's accounts and categories for filtering
    accounts = BankAccount.query.filter_by(user_id=current_user.id).all()
    categories = Category.query.all()
    
    return render_template('transactions.html', 
                           transactions=transactions,
                           accounts=accounts,
                           categories=categories,
                           filter_account_id=account_id,
                           filter_category_id=category_id,
                           filter_date_from=date_from,
                           filter_date_to=date_to)

@transactions_bp.route('/transactions/categorize', methods=['POST'])
@login_required
def categorize_transactions():
    # Get uncategorized transactions
    uncategorized = (Transaction.query
                   .join(BankAccount)
                   .filter(BankAccount.user_id == current_user.id)
                   .filter(Transaction.category_id == None)
                   .all())
    
    if not uncategorized:
        flash('No uncategorized transactions found.', 'info')
        return redirect(url_for('transactions.transactions'))
    
    count = 0
    # Categorize transactions
    for transaction in uncategorized:
        category_id = categorize_transaction(transaction.description, transaction.merchant)
        if category_id:
            transaction.category_id = category_id
            count += 1
    
    db.session.commit()
    
    flash(f'Successfully categorized {count} transactions.', 'success')
    return redirect(url_for('transactions.transactions'))

@transactions_bp.route('/transactions/analysis')
@login_required
def transaction_analysis():
    # Get all user transactions
    user_transactions = (Transaction.query
                        .join(BankAccount)
                        .filter(BankAccount.user_id == current_user.id)
                        .all())
    
    if not user_transactions:
        flash('No transactions available for analysis.', 'info')
        return redirect(url_for('transactions.transactions'))
    
    # Convert to DataFrame for analysis
    transactions_data = [{
        'amount': t.amount,
        'date': t.transaction_date,
        'description': t.description,
        'merchant': t.merchant,
        'category_id': t.category_id,
        'is_expense': t.is_expense
    } for t in user_transactions]
    
    df = pd.DataFrame(transactions_data)
    
    # Run analysis
    analysis_results = analyze_transactions(df)
    
    # Get categories for the report
    categories = {c.id: c.name for c in Category.query.all()}
    
    return render_template('transaction_analysis.html', 
                          results=analysis_results,
                          categories=categories)

@transactions_bp.route('/transactions/<int:transaction_id>/update_category', methods=['POST'])
@login_required
def update_transaction_category(transaction_id):
    category_id = request.form.get('category_id', type=int)
    
    # Validate transaction belongs to user
    transaction = (Transaction.query
                  .join(BankAccount)
                  .filter(BankAccount.user_id == current_user.id)
                  .filter(Transaction.id == transaction_id)
                  .first_or_404())
    
    # Update category
    transaction.category_id = category_id
    db.session.commit()
    
    flash('Transaction category updated successfully.', 'success')
    return redirect(url_for('transactions.transactions'))
