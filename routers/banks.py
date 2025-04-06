import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from models import BankAccount, Transaction
from services.bank_api import (
    get_supported_banks, 
    connect_to_bank, 
    fetch_account_data, 
    fetch_transactions,
    sync_account_data
)
from services.transaction_analyzer import categorize_transaction
from datetime import datetime

# Configure logger
logger = logging.getLogger(__name__)

banks_bp = Blueprint('banks', __name__)

@banks_bp.route('/banks')
@login_required
def bank_accounts():
    # Get user's bank accounts
    accounts = BankAccount.query.filter_by(user_id=current_user.id).all()
    
    return render_template('banks.html', accounts=accounts)

@banks_bp.route('/banks/connect', methods=['GET', 'POST'])
@login_required
def connect_bank():
    # Get list of supported banks
    supported_banks = get_supported_banks()
    
    if request.method == 'POST':
        bank_name = request.form.get('bank_name')
        credentials = {
            'username': request.form.get('username'),
            'password': request.form.get('password')
        }
        
        try:
            # Attempt to connect to bank API
            access_token = connect_to_bank(bank_name, credentials)
            
            if not access_token:
                flash('Failed to connect to bank. Please check your credentials.', 'danger')
                return redirect(url_for('banks.connect_bank'))
            
            # Get account information
            accounts_data = fetch_account_data(bank_name, access_token)
            
            # Save each account
            for account_data in accounts_data:
                # Check if account already exists
                existing_account = BankAccount.query.filter_by(
                    user_id=current_user.id,
                    bank_name=bank_name,
                    account_number=account_data['account_number']
                ).first()
                
                if existing_account:
                    # Update existing account
                    existing_account.balance = account_data['balance']
                    existing_account.currency = account_data['currency']
                    existing_account.access_token = access_token
                    existing_account.last_sync = datetime.utcnow()
                else:
                    # Create new account
                    new_account = BankAccount(
                        user_id=current_user.id,
                        bank_name=bank_name,
                        account_number=account_data['account_number'],
                        account_type=account_data['account_type'],
                        balance=account_data['balance'],
                        currency=account_data['currency'],
                        access_token=access_token,
                        last_sync=datetime.utcnow()
                    )
                    db.session.add(new_account)
            
            db.session.commit()
            
            # For each account, fetch transactions
            accounts = BankAccount.query.filter_by(
                user_id=current_user.id,
                bank_name=bank_name
            ).all()
            
            transaction_count = 0
            for account in accounts:
                transactions = fetch_transactions(bank_name, access_token, account.account_number)
                
                for transaction_data in transactions:
                    # Check if transaction already exists
                    existing_transaction = Transaction.query.filter_by(
                        external_id=transaction_data['external_id']
                    ).first()
                    
                    if not existing_transaction:
                        # Categorize transaction
                        category_id = categorize_transaction(
                            transaction_data['description'],
                            transaction_data.get('merchant', '')
                        )
                        
                        # Make sure we have a valid category_id
                        if category_id is None:
                            # Use the "Other" category if categorization fails
                            from models import Category
                            other_category = Category.query.filter_by(name="Другое").first()
                            if other_category:
                                category_id = other_category.id
                            else:
                                # If we somehow don't have an "Other" category, log error
                                logger.error("Failed to find 'Other' category")
                                continue
                        
                        # Create new transaction
                        new_transaction = Transaction(
                            account_id=account.id,
                            external_id=transaction_data['external_id'],
                            amount=transaction_data['amount'],
                            currency=transaction_data['currency'],
                            description=transaction_data['description'],
                            transaction_date=transaction_data['date'],
                            merchant=transaction_data.get('merchant', ''),
                            category_id=category_id,
                            is_expense=transaction_data['amount'] > 0
                        )
                        db.session.add(new_transaction)
                        transaction_count += 1
            
            db.session.commit()
            
            flash(f'Successfully connected to {bank_name} and imported {transaction_count} new transactions.', 'success')
            return redirect(url_for('banks.bank_accounts'))
            
        except Exception as e:
            flash(f'Error connecting to bank: {str(e)}', 'danger')
            return redirect(url_for('banks.connect_bank'))
    
    return render_template('connect_bank.html', banks=supported_banks)

@banks_bp.route('/banks/<int:account_id>/sync')
@login_required
def sync_bank_account(account_id):
    # Verify account belongs to user
    account = BankAccount.query.filter_by(
        id=account_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        # Sync account data
        new_balance, transaction_count = sync_account_data(
            account.bank_name,
            account.access_token,
            account.account_number,
            account.id
        )
        
        # Update account balance and sync time
        account.balance = new_balance
        account.last_sync = datetime.utcnow()
        db.session.commit()
        
        flash(f'Successfully synced account. Found {transaction_count} new transactions.', 'success')
    except Exception as e:
        flash(f'Error syncing account: {str(e)}', 'danger')
    
    return redirect(url_for('banks.bank_accounts'))

@banks_bp.route('/banks/<int:account_id>/delete', methods=['POST'])
@login_required
def delete_bank_account(account_id):
    # Verify account belongs to user
    account = BankAccount.query.filter_by(
        id=account_id,
        user_id=current_user.id
    ).first_or_404()
    
    # Delete account (cascade will delete associated transactions)
    db.session.delete(account)
    db.session.commit()
    
    flash('Bank account deleted successfully.', 'success')
    return redirect(url_for('banks.bank_accounts'))

@banks_bp.route('/recommendations')
@login_required
def recommendations():
    # Get user's recommendations
    from models import Recommendation
    recommendations = Recommendation.query.filter_by(user_id=current_user.id).order_by(Recommendation.created_at.desc()).all()
    
    # Generate new recommendations if none exist
    if not recommendations:
        from services.recommendation_engine import generate_recommendations
        generate_recommendations(current_user.id)
        recommendations = Recommendation.query.filter_by(user_id=current_user.id).order_by(Recommendation.created_at.desc()).all()
    
    return render_template('recommendations.html', recommendations=recommendations)

@banks_bp.route('/recommendations/generate', methods=['POST'])
@login_required
def generate_new_recommendations():
    from services.recommendation_engine import generate_recommendations
    count = generate_recommendations(current_user.id)
    
    flash(f'Generated {count} new recommendations for you.', 'success')
    return redirect(url_for('banks.recommendations'))
