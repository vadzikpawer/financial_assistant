from flask import Blueprint, render_template, flash
from flask_login import login_required, current_user
from models import BankAccount, Transaction, Recommendation, Category, SavingsGoal
from sqlalchemy import func
from app import db
from datetime import datetime, timedelta

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    # Get user's bank accounts
    accounts = BankAccount.query.filter_by(user_id=current_user.id).all()

    # Get total balance across all accounts
    total_balance = sum(account.balance for account in accounts)

    # Get latest transactions
    latest_transactions = (
        Transaction.query.join(BankAccount)
        .filter(BankAccount.user_id == current_user.id)
        .order_by(Transaction.transaction_date.desc())
        .limit(5)
        .all()
    )

    # Get recommendations
    recommendations = (
        Recommendation.query.filter_by(user_id=current_user.id)
        .order_by(Recommendation.created_at.desc())
        .limit(3)
        .all()
    )

    # Get savings goals
    savings_goals = (
        SavingsGoal.query.filter_by(user_id=current_user.id)
        .order_by(SavingsGoal.created_at.desc())
        .limit(3)
        .all()
    )

    # Get monthly spending by category (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    monthly_spending = (
        db.session.query(Category.name, func.sum(Transaction.amount).label("total"))
        .join(Transaction, Transaction.category_id == Category.id)
        .join(BankAccount, BankAccount.id == Transaction.account_id)
        .filter(BankAccount.user_id == current_user.id)
        .filter(Transaction.is_expense == True)
        .filter(Transaction.transaction_date >= thirty_days_ago)
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount).desc())
        .all()
    )

    # Format data for charts
    category_labels = [item[0] for item in monthly_spending]
    category_values = [float(item[1]) for item in monthly_spending]

    # Get daily spending (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)

    daily_spending = (
        db.session.query(
            func.date(Transaction.transaction_date).label("date"),
            func.sum(Transaction.amount).label("total"),
        )
        .join(BankAccount, BankAccount.id == Transaction.account_id)
        .filter(BankAccount.user_id == current_user.id)
        .filter(Transaction.is_expense == True)
        .filter(Transaction.transaction_date >= seven_days_ago)
        .group_by(func.date(Transaction.transaction_date))
        .order_by(func.date(Transaction.transaction_date))
        .all()
    )

    # Format data for charts
    daily_labels = [item[0].strftime("%d-%m") for item in daily_spending]
    daily_values = [float(item[1]) for item in daily_spending]

    return render_template(
        "dashboard.html",
        accounts=accounts,
        total_balance=total_balance,
        latest_transactions=latest_transactions,
        recommendations=recommendations,
        savings_goals=savings_goals,
        category_labels=category_labels,
        category_values=category_values,
        daily_labels=daily_labels,
        daily_values=daily_values,
    )
