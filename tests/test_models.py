import unittest
from datetime import datetime, timedelta
from app import app, db
from models import User, BankAccount, Transaction, Category, Recommendation, SavingsGoal


class TestUserModel(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["TESTING"] = True
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        """Test password hashing functionality"""
        user = User(username="test_user", email="test@example.com")
        user.set_password("password123")

        self.assertFalse(user.check_password("wrongpassword"))
        self.assertTrue(user.check_password("password123"))

    def test_user_creation(self):
        """Test user creation and retrieval"""
        user = User(username="test_user", email="test@example.com")
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()

        retrieved_user = User.query.filter_by(username="test_user").first()
        self.assertEqual(retrieved_user.email, "test@example.com")
        self.assertTrue(retrieved_user.check_password("password123"))

    def test_user_relationships(self):
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
        self.assertEqual(len(user.bank_accounts), 1)
        self.assertEqual(user.bank_accounts[0].bank_name, "Test Bank")

        self.assertEqual(len(user.recommendations), 1)
        self.assertEqual(user.recommendations[0].title, "Save on groceries")

        self.assertEqual(len(user.savings_goals), 1)
        self.assertEqual(user.savings_goals[0].title, "New Laptop")

        self.assertEqual(len(account.transactions), 1)
        self.assertEqual(account.transactions[0].description, "Grocery shopping")


class TestSavingsGoalModel(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["TESTING"] = True
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()

        # Create user
        self.user = User(username="test_user", email="test@example.com")
        self.user.set_password("password123")
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_progress_percentage(self):
        """Test progress percentage calculation"""
        goal = SavingsGoal(
            user_id=self.user.id,
            title="Vacation",
            target_amount=100000.0,
            current_amount=25000.0,
        )

        self.assertEqual(goal.progress_percentage(), 25)

        goal.current_amount = 50000.0
        self.assertEqual(goal.progress_percentage(), 50)

        goal.current_amount = 0.0
        self.assertEqual(goal.progress_percentage(), 0)

        goal.current_amount = 100000.0
        self.assertEqual(goal.progress_percentage(), 100)

    def test_days_remaining(self):
        """Test days remaining calculation"""
        # Test with future date
        future_date = datetime.utcnow() + timedelta(days=30)
        goal = SavingsGoal(
            user_id=self.user.id,
            title="Vacation",
            target_amount=100000.0,
            current_amount=0.0,
            target_date=future_date,
        )

        # Should be around 30 days, give or take 1 for test timing
        self.assertTrue(29 <= goal.days_remaining() <= 30)

        # Test with past date
        past_date = datetime.utcnow() - timedelta(days=10)
        goal.target_date = past_date
        self.assertEqual(goal.days_remaining(), 0)

        # Test with no target date
        goal.target_date = None
        self.assertIsNone(goal.days_remaining())

    def test_is_on_track(self):
        """Test is_on_track determination"""
        # Create a 100-day goal with linear progress expected
        today = datetime.utcnow()
        goal = SavingsGoal(
            user_id=self.user.id,
            title="Vacation",
            target_amount=100000.0,
            current_amount=0.0,
            start_date=today,
            target_date=today + timedelta(days=100),
        )

        # Day 0, 0% progress - on track
        self.assertTrue(goal.is_on_track())

        # Day 25, 25% progress - on track
        goal.start_date = today - timedelta(days=25)
        goal.current_amount = 25000.0
        self.assertTrue(goal.is_on_track())

        # Day 50, 40% progress - behind
        goal.start_date = today - timedelta(days=50)
        goal.current_amount = 40000.0
        self.assertFalse(goal.is_on_track())

        # Day 50, 60% progress - ahead
        goal.current_amount = 60000.0
        self.assertTrue(goal.is_on_track())

        # Achieved goal is on track
        goal.current_amount = 100000.0
        self.assertTrue(goal.is_on_track())
        self.assertTrue(goal.is_achieved)


if __name__ == "__main__":
    unittest.main()
