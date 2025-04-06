import unittest
from flask import url_for
from app import app, db
from models import User, BankAccount, Category, Transaction, Recommendation, SavingsGoal

class TestAuthRoutes(unittest.TestCase):

    def setUp(self):
        """Set up test environment"""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_index_route(self):
        """Test index route"""
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Check for expected content
        self.assertIn(b'FinAssistant', response.data)
    
    def test_login_route(self):
        """Test login functionality"""
        # Test GET request
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login', response.data)
        
        # Test successful login
        response = self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)
        
        # Test failed login - wrong password
        response = self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', response.data)
        
        # Test failed login - non-existent user
        response = self.app.post('/login', data={
            'email': 'nonexistent@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', response.data)
    
    def test_register_route(self):
        """Test registration functionality"""
        # Test GET request
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Register', response.data)
        
        # Test successful registration
        response = self.app.post('/register', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Account created successfully', response.data)
        
        # Verify user was created
        user = User.query.filter_by(email='newuser@example.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'newuser')
        
        # Test registration with existing email
        response = self.app.post('/register', data={
            'username': 'anotheruser',
            'email': 'test@example.com',  # This email is already registered
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b'Email already registered', response.data)
    
    def test_logout_route(self):
        """Test logout functionality"""
        # Login first
        self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Then logout
        response = self.app.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Successfully logged out', response.data)
        
        # Verify we're redirected to login after trying to access protected page
        response = self.app.get('/dashboard', follow_redirects=True)
        self.assertIn(b'Please log in to access this page', response.data)

class TestDashboardRoutes(unittest.TestCase):

    def setUp(self):
        """Set up test environment"""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        
        # Create test category
        self.category = Category(name='Food', icon='fa-utensils')
        db.session.add(self.category)
        
        db.session.commit()
        
        # Login
        self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
    
    def tearDown(self):
        """Clean up after tests"""
        self.app.get('/logout')
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_dashboard_route(self):
        """Test dashboard page with no accounts"""
        response = self.app.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Dashboard', response.data)
        self.assertIn(b'Connect your bank accounts', response.data)
    
    def test_dashboard_with_data(self):
        """Test dashboard with bank accounts and transactions"""
        # Create bank account
        account = BankAccount(
            user_id=self.user.id,
            bank_name='Test Bank',
            account_number='12345678',
            account_type='Checking',
            balance=1000.0,
            currency='RUB'
        )
        db.session.add(account)
        db.session.commit()
        
        # Create transactions
        transaction1 = Transaction(
            account_id=account.id,
            amount=100.0,
            currency='RUB',
            description='Grocery shopping',
            transaction_date=datetime.utcnow(),
            merchant='Supermarket',
            category_id=self.category.id,
            is_expense=True
        )
        
        transaction2 = Transaction(
            account_id=account.id,
            amount=50.0,
            currency='RUB',
            description='Restaurant',
            transaction_date=datetime.utcnow(),
            merchant='Local Cafe',
            category_id=self.category.id,
            is_expense=True
        )
        
        db.session.add_all([transaction1, transaction2])
        db.session.commit()
        
        # Access dashboard
        response = self.app.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        
        # Check for account data
        self.assertIn(b'Test Bank', response.data)
        self.assertIn(b'1000', response.data)
        
        # Transactions should appear in latest transactions section
        self.assertIn(b'Grocery shopping', response.data)
        self.assertIn(b'Restaurant', response.data)

class TestSavingsGoalRoutes(unittest.TestCase):

    def setUp(self):
        """Set up test environment"""
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()
        
        # Login
        self.app.post('/login', data={
            'email': 'test@example.com',
            'password': 'password123'
        })
    
    def tearDown(self):
        """Clean up after tests"""
        self.app.get('/logout')
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_savings_goals_route(self):
        """Test savings goals page with no goals"""
        response = self.app.get('/savings_goals')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Savings Goals', response.data)
        self.assertIn(b'You don\'t have any savings goals yet', response.data)
    
    def test_new_savings_goal_route(self):
        """Test creating a new savings goal"""
        # Test GET request
        response = self.app.get('/savings_goals/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create New Savings Goal', response.data)
        
        # Test POST request
        response = self.app.post('/savings_goals/new', data={
            'title': 'Vacation',
            'description': 'Summer vacation to the beach',
            'target_amount': 50000,
            'target_date': '2025-08-01',
            'character_type': 'bogatyr'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Savings goal created successfully', response.data)
        
        # Verify goal was created
        goal = SavingsGoal.query.filter_by(title='Vacation').first()
        self.assertIsNotNone(goal)
        self.assertEqual(goal.target_amount, 50000)
        self.assertEqual(goal.character_type, 'bogatyr')
    
    def test_view_savings_goal_route(self):
        """Test viewing a savings goal"""
        # Create a savings goal
        goal = SavingsGoal(
            user_id=self.user.id,
            title='New Car',
            description='Save for a new car',
            target_amount=500000.0,
            current_amount=100000.0,
            character_type='firebird'
        )
        db.session.add(goal)
        db.session.commit()
        
        # Test viewing the goal
        response = self.app.get(f'/savings_goals/{goal.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'New Car', response.data)
        self.assertIn(b'500000', response.data)
        self.assertIn(b'100000', response.data)
        self.assertIn(b'20%', response.data)  # Progress calculation
    
    def test_update_amount_route(self):
        """Test updating the amount for a savings goal"""
        # Create a savings goal
        goal = SavingsGoal(
            user_id=self.user.id,
            title='New Car',
            description='Save for a new car',
            target_amount=500000.0,
            current_amount=100000.0
        )
        db.session.add(goal)
        db.session.commit()
        
        # Test updating the amount
        response = self.app.post(f'/savings_goals/{goal.id}/update_amount', data={
            'amount': 50000
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify amount was updated
        updated_goal = SavingsGoal.query.get(goal.id)
        self.assertEqual(updated_goal.current_amount, 150000.0)  # 100000 + 50000
        
        # Test completion of goal
        response = self.app.post(f'/savings_goals/{goal.id}/update_amount', data={
            'amount': 350000
        }, follow_redirects=True)
        
        # Verify goal is marked as achieved
        completed_goal = SavingsGoal.query.get(goal.id)
        self.assertTrue(completed_goal.is_achieved)
        self.assertEqual(completed_goal.current_amount, 500000.0)
    
    def test_delete_savings_goal_route(self):
        """Test deleting a savings goal"""
        # Create a savings goal
        goal = SavingsGoal(
            user_id=self.user.id,
            title='New Car',
            description='Save for a new car',
            target_amount=500000.0,
            current_amount=100000.0
        )
        db.session.add(goal)
        db.session.commit()
        
        # Test deleting the goal
        response = self.app.get(f'/savings_goals/{goal.id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Savings goal deleted successfully', response.data)
        
        # Verify goal was deleted
        deleted_goal = SavingsGoal.query.get(goal.id)
        self.assertIsNone(deleted_goal)

if __name__ == '__main__':
    unittest.main()
