import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app import app, db
from models import User, BankAccount, Transaction, Category, Recommendation
from services.transaction_analyzer import (
    init_categories,
    categorize_transaction,
    analyze_transactions,
)
from services.bank_api import get_supported_banks, generate_sample_transactions
from services.ai_recommendation import get_rule_based_recommendations


class TestTransactionAnalyzer(unittest.TestCase):
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

    def test_init_categories(self):
        """Test category initialization"""
        init_categories()

        # Check if categories were created
        categories = Category.query.all()
        self.assertGreater(len(categories), 0)

        # Check for some expected categories
        category_names = [c.name for c in categories]
        self.assertIn("Продукты", category_names)
        self.assertIn("Рестораны", category_names)
        self.assertIn("Транспорт", category_names)

    def test_categorize_transaction(self):
        """Test transaction categorization"""
        # Initialize categories first
        init_categories()

        # Test food category
        food_category_id = categorize_transaction("Супермаркет", "Пятерочка")
        food_category = Category.query.get(food_category_id)
        self.assertEqual(food_category.name, "Продукты")

        # Test restaurant category
        restaurant_category_id = categorize_transaction("Ресторан", "KFC")
        restaurant_category = Category.query.get(restaurant_category_id)
        self.assertEqual(restaurant_category.name, "Рестораны")

        # Test transport category
        transport_category_id = categorize_transaction(
            "Проезд в метро", "Московский метрополитен"
        )
        transport_category = Category.query.get(transport_category_id)
        self.assertEqual(transport_category.name, "Транспорт")

    def test_analyze_transactions(self):
        """Test transaction analysis"""
        # Create test data
        import pandas as pd

        # Create test transactions dataframe
        data = {
            "amount": [100.0, 200.0, 300.0, 400.0, 500.0],
            "category_name": [
                "Продукты",
                "Рестораны",
                "Продукты",
                "Транспорт",
                "Развлечения",
            ],
            "transaction_date": [
                datetime(2023, 1, 1),
                datetime(2023, 1, 2),
                datetime(2023, 1, 3),
                datetime(2023, 1, 4),
                datetime(2023, 1, 5),
            ],
            "is_expense": [True, True, True, True, True],
        }
        df = pd.DataFrame(data)

        # Test analysis
        results = analyze_transactions(df)

        # Check for expected metrics
        self.assertIn("total_spending", results)
        self.assertIn("category_spending", results)
        self.assertIn("daily_spending", results)

        # Check total spending
        self.assertEqual(results["total_spending"], 1500.0)

        # Check category spending
        category_spending = results["category_spending"]
        self.assertEqual(category_spending["Продукты"], 400.0)
        self.assertEqual(category_spending["Рестораны"], 200.0)
        self.assertEqual(category_spending["Транспорт"], 400.0)
        self.assertEqual(category_spending["Развлечения"], 500.0)


class TestBankAPI(unittest.TestCase):
    def test_get_supported_banks(self):
        """Test getting supported banks"""
        banks = get_supported_banks()
        self.assertIsInstance(banks, list)
        self.assertGreater(len(banks), 0)

        # Check for expected banks
        bank_names = [bank["name"] for bank in banks]
        self.assertIn("Тинькофф", bank_names)
        self.assertIn("Сбербанк", bank_names)

    def test_generate_sample_transactions(self):
        """Test generating sample transactions"""
        transactions = generate_sample_transactions("Тинькофф", "12345678", days=10)

        # Check transactions structure
        self.assertIsInstance(transactions, list)
        self.assertGreater(len(transactions), 0)

        # Check transaction properties
        for transaction in transactions:
            self.assertIn("external_id", transaction)
            self.assertIn("amount", transaction)
            self.assertIn("currency", transaction)
            self.assertIn("description", transaction)
            self.assertIn("transaction_date", transaction)
            self.assertIn("merchant", transaction)

            # Check types
            self.assertIsInstance(transaction["amount"], float)
            self.assertIsInstance(transaction["description"], str)
            self.assertIsInstance(transaction["transaction_date"], datetime)


class TestAIRecommendation(unittest.TestCase):
    def test_rule_based_recommendations(self):
        """Test rule-based recommendations generator"""
        # Test financial data
        financial_data = {
            "total_spending": 50000.0,
            "category_spending": {
                "Продукты": 15000.0,
                "Рестораны": 10000.0,
                "Транспорт": 5000.0,
                "Развлечения": 8000.0,
                "Коммунальные платежи": 12000.0,
            },
            "daily_spending": {
                "2023-01-01": 1000.0,
                "2023-01-02": 2000.0,
                "2023-01-03": 1500.0,
                "2023-01-04": 3000.0,
                "2023-01-05": 2500.0,
            },
            "monthly_income": 100000.0,
        }

        # Generate recommendations
        recommendations = get_rule_based_recommendations(financial_data)

        # Check recommendations structure
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

        # Check recommendation properties
        for recommendation in recommendations:
            self.assertIn("title", recommendation)
            self.assertIn("description", recommendation)
            self.assertIn("potential_savings", recommendation)

            # Check types
            self.assertIsInstance(recommendation["title"], str)
            self.assertIsInstance(recommendation["description"], str)
            self.assertIsInstance(recommendation["potential_savings"], (int, float))

            # Check non-empty values
            self.assertGreater(len(recommendation["title"]), 0)
            self.assertGreater(len(recommendation["description"]), 0)

            # Potential savings should be reasonable
            self.assertGreaterEqual(recommendation["potential_savings"], 0)
            self.assertLessEqual(
                recommendation["potential_savings"], financial_data["total_spending"]
            )

    @patch("services.ai_recommendation.requests.post")
    def test_api_error_handling(self, mock_post):
        """Test handling of API errors"""
        # Mock a failed API call
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal server error"}
        mock_post.return_value = mock_response

        # Test financial data
        financial_data = {
            "total_spending": 50000.0,
            "category_spending": {"Продукты": 15000.0, "Рестораны": 10000.0},
            "monthly_income": 100000.0,
        }

        # Should fall back to rule-based recommendations
        recommendations = get_rule_based_recommendations(financial_data, api_error=True)

        # Still should get recommendations
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)


if __name__ == "__main__":
    unittest.main()
