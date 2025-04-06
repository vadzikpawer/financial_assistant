import pytest
from datetime import datetime, timedelta
from models import User, BankAccount, Transaction, Category, Recommendation, SavingsGoal
from app import db

pytestmark = pytest.mark.models


def test_password_hashing(app_context):
    """Test password hashing functionality"""
    user = User(username="test_user", email="test@example.com")
    user.set_password("password123")

    assert not user.check_password("wrongpassword")
    assert user.check_password("password123")


def test_user_creation(app_context):
    """Test user creation and retrieval"""
    user = User(username="test_user", email="test@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    retrieved_user = User.query.filter_by(username="test_user").first()
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.check_password("password123")


def test_user_relationships(app_context):
    """Test user relationships with other entities"""
    # Create user
    user = User(username="test_user", email="test@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()

    # Create bank account
    account = BankAccount(
        user_id=user.id,
        bank_name="Test Bank",
        account_number="12345678",
        account_type="Checking",
        balance=1000.0,
        currency="RUB",
    )
    db.session.add(account)

    # Create category
    category = Category(name="Food", icon="fa-utensils")
    db.session.add(category)
    db.session.commit()

    # Create transaction
    transaction = Transaction(
        account_id=account.id,
        amount=100.0,
        currency="RUB",
        description="Grocery shopping",
        transaction_date=datetime.utcnow(),
        merchant="Supermarket",
        category_id=category.id,
        is_expense=True,
    )
    db.session.add(transaction)

    # Create recommendation
    recommendation = Recommendation(
        user_id=user.id,
        title="Save on groceries",
        description="Consider buying in bulk to save money",
        potential_savings=500.0,
        category_id=category.id,
    )
    db.session.add(recommendation)

    # Create savings goal
    savings_goal = SavingsGoal(
        user_id=user.id,
        title="New Laptop",
        description="Save for a new laptop",
        target_amount=50000.0,
        current_amount=10000.0,
        target_date=datetime.utcnow() + timedelta(days=90),
    )
    db.session.add(savings_goal)
    db.session.commit()

    # Test relationships
    assert len(user.bank_accounts) == 1
    assert user.bank_accounts[0].bank_name == "Test Bank"

    assert len(user.recommendations) == 1
    assert user.recommendations[0].title == "Save on groceries"

    assert len(user.savings_goals) == 1
    assert user.savings_goals[0].title == "New Laptop"

    assert len(account.transactions) == 1
    assert account.transactions[0].description == "Grocery shopping"


def test_progress_percentage(app_context, test_user):
    """Test progress percentage calculation"""
    goal = SavingsGoal(
        user_id=test_user.id,
        title="Vacation",
        target_amount=100000.0,
        current_amount=25000.0,
    )

    assert goal.progress_percentage() == 25

    goal.current_amount = 50000.0
    assert goal.progress_percentage() == 50

    goal.current_amount = 0.0
    assert goal.progress_percentage() == 0

    goal.current_amount = 100000.0
    assert goal.progress_percentage() == 100


def test_days_remaining(app_context, test_user):
    """Test days remaining calculation"""
    # Test with future date
    future_date = datetime.utcnow() + timedelta(days=30)
    goal = SavingsGoal(
        user_id=test_user.id,
        title="Vacation",
        target_amount=100000.0,
        current_amount=0.0,
        target_date=future_date,
    )

    # Should be around 30 days, give or take 1 for test timing
    assert 29 <= goal.days_remaining() <= 30

    # Test with past date
    past_date = datetime.utcnow() - timedelta(days=10)
    goal.target_date = past_date
    assert goal.days_remaining() == 0

    # Test with no target date
    goal.target_date = None
    assert goal.days_remaining() is None


def test_is_on_track(app_context, test_user):
    """Test is_on_track determination"""
    # Create a 100-day goal with linear progress expected
    today = datetime.utcnow()
    goal = SavingsGoal(
        user_id=test_user.id,
        title="Vacation",
        target_amount=100000.0,
        current_amount=0.0,
        start_date=today,
        target_date=today + timedelta(days=100),
    )

    # Day 0, 0% progress - on track
    assert goal.is_on_track()

    # Day 25, 25% progress - on track
    goal.start_date = today - timedelta(days=25)
    goal.current_amount = 25000.0
    assert goal.is_on_track()

    # Day 50, 40% progress - behind
    goal.start_date = today - timedelta(days=50)
    goal.current_amount = 40000.0
    assert not goal.is_on_track()

    # Day 50, 60% progress - ahead
    goal.current_amount = 60000.0
    assert goal.is_on_track()

    # Achieved goal is on track
    goal.current_amount = 100000.0
    assert goal.is_on_track()
    assert goal.is_achieved
