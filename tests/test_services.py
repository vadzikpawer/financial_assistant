import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
import pandas as pd
from models import Category
from services.transaction_analyzer import (
    init_categories,
    categorize_transaction,
    analyze_transactions,
)
from services.bank_api import get_supported_banks, generate_sample_transactions
from services.ai_recommendation import get_rule_based_recommendations
from app import db

pytestmark = pytest.mark.services


def test_init_categories(app_context):
    """Test category initialization"""
    init_categories()

    # Check if categories were created
    categories = Category.query.all()
    assert len(categories) > 0

    # Check for some expected categories
    category_names = [c.name for c in categories]
    assert "Продукты" in category_names
    assert "Рестораны" in category_names
    assert "Транспорт" in category_names


def test_categorize_transaction(app_context):
    """Test transaction categorization"""
    # Initialize categories first
    init_categories()

    # Test food category
    food_category_id = categorize_transaction("Супермаркет", "Пятерочка")
    food_category = Category.query.get(food_category_id)
    assert food_category.name == "Продукты"

    # Test restaurant category
    restaurant_category_id = categorize_transaction("Ресторан", "KFC")
    restaurant_category = Category.query.get(restaurant_category_id)
    assert restaurant_category.name == "Рестораны"

    # Test transport category
    transport_category_id = categorize_transaction(
        "Проезд в метро", "Московский метрополитен"
    )
    transport_category = Category.query.get(transport_category_id)
    assert transport_category.name == "Транспорт"


def test_analyze_transactions(app_context):
    """Test transaction analysis"""
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
    assert "total_spending" in results
    assert "category_spending" in results
    assert "daily_spending" in results

    # Check total spending
    assert results["total_spending"] == 1500.0

    # Check category spending
    category_spending = results["category_spending"]
    assert category_spending["Продукты"] == 400.0
    assert category_spending["Рестораны"] == 200.0
    assert category_spending["Транспорт"] == 400.0
    assert category_spending["Развлечения"] == 500.0


def test_get_supported_banks():
    """Test getting supported banks"""
    banks = get_supported_banks()
    assert isinstance(banks, list)
    assert len(banks) > 0

    # Check for expected banks
    bank_names = [bank["name"] for bank in banks]
    assert "Тинькофф" in bank_names
    assert "Сбербанк" in bank_names


def test_generate_sample_transactions():
    """Test generating sample transactions"""
    transactions = generate_sample_transactions("Тинькофф", "12345678", days=10)

    # Check transactions structure
    assert isinstance(transactions, list)
    assert len(transactions) > 0

    # Check transaction properties
    for transaction in transactions:
        assert "external_id" in transaction
        assert "amount" in transaction
        assert "currency" in transaction
        assert "description" in transaction
        assert "transaction_date" in transaction
        assert "merchant" in transaction

        # Check types
        assert isinstance(transaction["amount"], float)
        assert isinstance(transaction["description"], str)
        assert isinstance(transaction["transaction_date"], datetime)


def test_rule_based_recommendations():
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
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0

    # Check recommendation properties
    for recommendation in recommendations:
        assert "title" in recommendation
        assert "description" in recommendation
        assert "potential_savings" in recommendation

        # Check types
        assert isinstance(recommendation["title"], str)
        assert isinstance(recommendation["description"], str)
        assert isinstance(recommendation["potential_savings"], (int, float))

        # Check non-empty values
        assert len(recommendation["title"]) > 0
        assert len(recommendation["description"]) > 0

        # Potential savings should be reasonable
        assert recommendation["potential_savings"] >= 0
        assert recommendation["potential_savings"] <= financial_data["total_spending"]


@patch("services.ai_recommendation.requests.post")
def test_api_error_handling(mock_post):
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
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
