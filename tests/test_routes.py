import pytest
import datetime
from flask import url_for
from models import User, BankAccount, Category, Transaction, Recommendation, SavingsGoal
from app import db

pytestmark = pytest.mark.routes


def test_index_route(client):
    """Test index route"""
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    # Check for expected content
    assert b"FinAssistant" in response.data


def test_login_route(client, test_user):
    """Test login functionality"""
    # Test GET request
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data

    # Test successful login
    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "password123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Dashboard" in response.data

    # Test failed login - wrong password
    response = client.post(
        "/login",
        data={"email": "test@example.com", "password": "wrongpassword"},
        follow_redirects=True,
    )
    assert b"Invalid email or password" in response.data

    # Test failed login - non-existent user
    response = client.post(
        "/login",
        data={"email": "nonexistent@example.com", "password": "password123"},
        follow_redirects=True,
    )
    assert b"Invalid email or password" in response.data


def test_register_route(client):
    """Test registration functionality"""
    # Test GET request
    response = client.get("/register")
    assert response.status_code == 200
    assert b"Register" in response.data

    # Test successful registration
    response = client.post(
        "/register",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert b"Account created successfully" in response.data

    # Verify user was created
    user = User.query.filter_by(email="newuser@example.com").first()
    assert user is not None
    assert user.username == "newuser"

    # Test registration with existing email
    response = client.post(
        "/register",
        data={
            "username": "anotheruser",
            "email": "test@example.com",  # This email is already registered
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True,
    )
    assert b"Email already registered" in response.data


def test_logout_route(client, test_user):
    """Test logout functionality"""
    # Login first
    client.post(
        "/login", data={"email": "test@example.com", "password": "password123"}
    )

    # Then logout
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Successfully logged out" in response.data

    # Verify we're redirected to login after trying to access protected page
    response = client.get("/dashboard", follow_redirects=True)
    assert b"Please log in to access this page" in response.data


def test_dashboard_route(authenticated_client):
    """Test dashboard page with no accounts"""
    response = authenticated_client.get("/dashboard")
    assert response.status_code == 200
    assert b"Dashboard" in response.data
    assert b"Connect your bank accounts" in response.data


def test_dashboard_with_data(authenticated_client, test_user, test_category):
    """Test dashboard with bank accounts and transactions"""
    # Create bank account
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

    # Create transactions
    transaction1 = Transaction(
        account_id=account.id,
        amount=100.0,
        currency="RUB",
        description="Grocery shopping",
        transaction_date=datetime.datetime.utcnow(),
        merchant="Supermarket",
        category_id=test_category.id,
        is_expense=True,
    )

    transaction2 = Transaction(
        account_id=account.id,
        amount=50.0,
        currency="RUB",
        description="Restaurant",
        transaction_date=datetime.datetime.utcnow(),
        merchant="Local Cafe",
        category_id=test_category.id,
        is_expense=True,
    )

    db.session.add_all([transaction1, transaction2])
    db.session.commit()

    # Access dashboard
    response = authenticated_client.get("/dashboard")
    assert response.status_code == 200

    # Check for account data
    assert b"Test Bank" in response.data
    assert b"1000" in response.data

    # Transactions should appear in latest transactions section
    assert b"Grocery shopping" in response.data
    assert b"Restaurant" in response.data


def test_savings_goals_route(authenticated_client):
    """Test savings goals page with no goals"""
    response = authenticated_client.get("/savings_goals")
    assert response.status_code == 200
    assert b"Savings Goals" in response.data
    assert b"You don't have any savings goals yet" in response.data


def test_new_savings_goal_route(authenticated_client, test_user):
    """Test creating a new savings goal"""
    # Test GET request
    response = authenticated_client.get("/savings_goals/new")
    assert response.status_code == 200
    assert b"Create New Savings Goal" in response.data

    # Test POST request
    response = authenticated_client.post(
        "/savings_goals/new",
        data={
            "title": "Vacation",
            "description": "Summer vacation to the beach",
            "target_amount": 50000,
            "target_date": "2025-08-01",
            "character_type": "bogatyr",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Savings goal created successfully" in response.data

    # Verify goal was created
    goal = SavingsGoal.query.filter_by(title="Vacation").first()
    assert goal is not None
    assert goal.target_amount == 50000
    assert goal.character_type == "bogatyr"


def test_view_savings_goal_route(authenticated_client, test_savings_goal):
    """Test viewing a savings goal"""
    # Test viewing the goal
    response = authenticated_client.get(f"/savings_goals/{test_savings_goal.id}")
    assert response.status_code == 200
    assert b"New Car" in response.data
    assert b"500000" in response.data
    assert b"100000" in response.data
    assert b"20%" in response.data  # Progress calculation


def test_update_amount_route(authenticated_client, test_user):
    """Test updating the amount for a savings goal"""
    # Create a savings goal
    goal = SavingsGoal(
        user_id=test_user.id,
        title="New Car",
        description="Save for a new car",
        target_amount=500000.0,
        current_amount=100000.0,
    )
    db.session.add(goal)
    db.session.commit()

    # Test updating the amount
    response = authenticated_client.post(
        f"/savings_goals/{goal.id}/update_amount",
        data={"amount": 50000},
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verify amount was updated
    updated_goal = SavingsGoal.query.get(goal.id)
    assert updated_goal.current_amount == 150000.0  # 100000 + 50000

    # Test completion of goal
    response = authenticated_client.post(
        f"/savings_goals/{goal.id}/update_amount",
        data={"amount": 350000},
        follow_redirects=True,
    )

    # Verify goal is marked as achieved
    completed_goal = SavingsGoal.query.get(goal.id)
    assert completed_goal.is_achieved
    assert completed_goal.current_amount == 500000.0


def test_delete_savings_goal_route(authenticated_client, test_user):
    """Test deleting a savings goal"""
    # Create a savings goal
    goal = SavingsGoal(
        user_id=test_user.id,
        title="New Car",
        description="Save for a new car",
        target_amount=500000.0,
        current_amount=100000.0,
    )
    db.session.add(goal)
    db.session.commit()

    # Test deleting the goal
    response = authenticated_client.get(
        f"/savings_goals/{goal.id}/delete", follow_redirects=True
    )
    assert response.status_code == 200
    assert b"Savings goal deleted successfully" in response.data

    # Verify goal was deleted
    deleted_goal = SavingsGoal.query.get(goal.id)
    assert deleted_goal is None
