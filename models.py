from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    bank_accounts = db.relationship(
        "BankAccount", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    recommendations = db.relationship(
        "Recommendation", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    savings_goals = db.relationship(
        "SavingsGoal", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"


class BankAccount(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(100), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)
    access_token = db.Column(db.String(1000))
    balance = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default="RUB")
    last_sync = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    transactions = db.relationship(
        "Transaction", backref="account", lazy=True, cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<BankAccount {self.bank_name} {self.account_number}>"


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey("bank_account.id"), nullable=False)
    external_id = db.Column(db.String(100), nullable=True, unique=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default="RUB")
    description = db.Column(db.String(255))
    transaction_date = db.Column(db.DateTime, nullable=False)
    merchant = db.Column(db.String(100))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    is_expense = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transaction {self.amount} {self.currency} - {self.description}>"


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50))

    # Relationships
    transactions = db.relationship("Transaction", backref="category", lazy=True)

    def __repr__(self):
        return f"<Category {self.name}>"


class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    potential_savings = db.Column(db.Float)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    category = db.relationship("Category")

    def __repr__(self):
        return f"<Recommendation {self.title}>"


class SavingsGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_amount = db.Column(db.Float, nullable=False)
    current_amount = db.Column(db.Float, default=0.0)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    target_date = db.Column(db.DateTime, nullable=True)
    character_type = db.Column(db.String(50), default="bogatyr")  # Russian knight
    is_achieved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Helper properties
    @property
    def progress_percentage(self):
        if self.target_amount <= 0:
            return 100
        progress = (self.current_amount / self.target_amount) * 100
        return min(100, max(0, progress))  # Clamp between 0 and 100

    @property
    def days_remaining(self):
        if not self.target_date:
            return None
        delta = self.target_date - datetime.utcnow()
        return max(0, delta.days)

    @property
    def is_on_track(self):
        if not self.target_date or self.target_amount <= 0:
            return True

        # Calculate the expected progress based on time elapsed
        total_days = (self.target_date - self.start_date).days
        if total_days <= 0:
            return self.progress_percentage >= 100

        days_elapsed = (datetime.utcnow() - self.start_date).days
        expected_progress = (days_elapsed / total_days) * 100

        # User is on track if their progress is at least 90% of expected
        return self.progress_percentage >= (expected_progress * 0.9)

    def __repr__(self):
        return f"<SavingsGoal {self.title}: {self.current_amount}/{self.target_amount}>"
