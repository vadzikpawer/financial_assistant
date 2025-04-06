import pytest
from datetime import datetime
from app import app, db
from models import User, BankAccount, Category, Transaction, Recommendation, SavingsGoal


@pytest.fixture(scope="function")
def app_context():
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    
    ctx = app.app_context()
    ctx.push()
    db.create_all()
    
    yield app
    
    db.session.remove()
    db.drop_all()
    ctx.pop()


@pytest.fixture(scope="function")
def client(app_context):
    return app_context.test_client()


@pytest.fixture(scope="function")
def test_user(app_context):
    user = User(username="testuser", email="test@example.com")
    user.set_password("password123")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture(scope="function")
def test_category(app_context):
    category = Category(name="Food", icon="fa-utensils")
    db.session.add(category)
    db.session.commit()
    return category


@pytest.fixture(scope="function")
def test_bank_account(app_context, test_user):
    account = BankAccount(
        user_id=test_user.id,
        bank_name="Test Bank",
        account_number="12345678",
        account_type="Checking",
        balance=1000.0,
        currency="RUB",
    )
    db.session.add(account)
    db.session.commit()
    return account


@pytest.fixture(scope="function")
def authenticated_client(client, test_user):
    client.post(
        "/login", 
        data={"email": "test@example.com", "password": "password123"}
    )
    return client


@pytest.fixture(scope="function")
def test_transaction(app_context, test_bank_account, test_category):
    transaction = Transaction(
        account_id=test_bank_account.id,
        amount=100.0,
        currency="RUB",
        description="Grocery shopping",
        transaction_date=datetime.utcnow(),
        merchant="Supermarket",
        category_id=test_category.id,
        is_expense=True,
    )
    db.session.add(transaction)
    db.session.commit()
    return transaction


@pytest.fixture(scope="function")
def test_savings_goal(app_context, test_user):
    goal = SavingsGoal(
        user_id=test_user.id,
        title="New Car",
        description="Save for a new car",
        target_amount=500000.0,
        current_amount=100000.0,
        character_type="firebird",
    )
    db.session.add(goal)
    db.session.commit()
    return goal