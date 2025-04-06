import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from app import db
from models import Category

logger = logging.getLogger(__name__)

# Category mapping - for demo purposes
# In a real app, this would be replaced with a proper ML model
CATEGORY_KEYWORDS = {
    "Продукты": ["пятёрочка", "магнит", "перекрёсток", "лента", "ашан", "metro", "продукты"],
    "Рестораны": ["кафе", "ресторан", "dodo", "пицца", "starbucks", "kfc", "mcdonald", "бургер", "суши"],
    "Транспорт": ["такси", "яндекс.такси", "uber", "метро", "автобус", "трамвай", "троллейбус", "аэро", "жд"],
    "Шоппинг": ["wildberries", "ozon", "zara", "h&m", "спортмастер", "покупка", "детский мир"],
    "Развлечения": ["кино", "театр", "концерт", "музей", "okko", "netflix", "подписка"],
    "Здоровье": ["аптека", "36.6", "клиника", "больница", "доктор", "врач", "стоматолог"],
    "Связь": ["мобильная связь", "интернет", "телефон", "мтс", "билайн", "мегафон", "tele2"],
    "Жильё": ["аренда", "квартплата", "жкх", "электричество", "газ", "вода"],
    "Техника": ["м.видео", "эльдорадо", "dns", "citilink"],
    "Топливо": ["азс", "газпром", "лукойл", "роснефть", "бензин"]
}

def init_categories():
    """Initialize categories in the database if they don't exist"""
    try:
        # Check if categories exist
        category_count = Category.query.count()
        
        # Log current state
        logger.debug(f"Checking categories: found {category_count} existing categories")
        
        # Create default categories dictionary with icons
        default_categories = {}
        for category_name in CATEGORY_KEYWORDS.keys():
            icon = get_category_icon(category_name)
            default_categories[category_name] = icon
        
        # Add special categories
        default_categories["Другое"] = "question-circle"
        default_categories["Доход"] = "arrow-down"
        
        if category_count == 0:
            # Create all categories if none exist
            for category_name, icon in default_categories.items():
                category = Category(name=category_name, icon=icon)
                db.session.add(category)
                
            db.session.commit()
            logger.info(f"Initialized {len(default_categories)} categories from scratch")
            return True
        else:
            # Check for any missing categories and add them
            existing_categories = {cat.name: cat for cat in Category.query.all()}
            categories_added = 0
            
            for category_name, icon in default_categories.items():
                if category_name not in existing_categories:
                    category = Category(name=category_name, icon=icon)
                    db.session.add(category)
                    categories_added += 1
            
            if categories_added > 0:
                db.session.commit()
                logger.info(f"Added {categories_added} missing categories")
            else:
                logger.debug("All categories already exist, nothing to add")
            
            return True
    except Exception as e:
        logger.error(f"Error initializing categories: {str(e)}")
        db.session.rollback()
        return False

def get_category_icon(category_name):
    """Get appropriate icon for category"""
    category_icons = {
        "Продукты": "cart",
        "Рестораны": "utensils",
        "Транспорт": "car",
        "Шоппинг": "shopping-bag",
        "Развлечения": "film",
        "Здоровье": "heart",
        "Связь": "phone",
        "Жильё": "home",
        "Техника": "laptop",
        "Топливо": "gas-pump",
        "Другое": "question-circle",
        "Доход": "arrow-down"
    }
    
    return category_icons.get(category_name, "tag")

def categorize_transaction(description, merchant):
    """
    Categorize a transaction based on description and merchant
    
    Args:
        description (str): Transaction description
        merchant (str): Merchant name
        
    Returns:
        int: Category ID
    """
    try:
        # Initialize categories if they don't exist
        init_categories()
        
        # Get text to check (combine description and merchant)
        text = f"{description} {merchant}".lower()
        
        # Check if this is income
        income_keywords = ["зачисление", "перевод от"]
        if any(keyword in text for keyword in income_keywords):
            income_category = Category.query.filter_by(name="Доход").first()
            if income_category:
                return income_category.id
        
        # Match against category keywords
        for category_name, keywords in CATEGORY_KEYWORDS.items():
            if any(keyword.lower() in text for keyword in keywords):
                category = Category.query.filter_by(name=category_name).first()
                if category:
                    return category.id
        
        # If no match found, use "Other" category
        other_category = Category.query.filter_by(name="Другое").first()
        if other_category:
            return other_category.id
        
        return None
    except Exception as e:
        logger.error(f"Error categorizing transaction: {str(e)}")
        return None

def analyze_transactions(transactions_df):
    """
    Analyze transactions to extract insights
    
    Args:
        transactions_df (DataFrame): DataFrame of transactions
        
    Returns:
        dict: Analysis results
    """
    try:
        # Make a copy to avoid modifying the original
        df = transactions_df.copy()
        
        # Convert date to datetime if it's not already
        if not pd.api.types.is_datetime64_any_dtype(df['date']):
            df['date'] = pd.to_datetime(df['date'])
        
        # Get categories
        categories = {c.id: c.name for c in Category.query.all()}
        
        # Add category name to DataFrame
        df['category_name'] = df['category_id'].map(categories)
        
        # Filter for expenses only for some analyses
        expenses_df = df[df['is_expense'] == True]
        
        # Calculate date ranges
        today = datetime.now()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_prev_month = (start_of_month - timedelta(days=1)).replace(day=1)
        
        # Calculate basic stats
        total_spent = expenses_df['amount'].sum()
        total_income = df[df['is_expense'] == False]['amount'].sum()
        
        # Current month spending
        current_month_expenses = expenses_df[expenses_df['date'] >= start_of_month]
        current_month_spent = current_month_expenses['amount'].sum() if not current_month_expenses.empty else 0
        
        # Previous month spending
        prev_month_expenses = expenses_df[(expenses_df['date'] >= start_of_prev_month) & 
                                         (expenses_df['date'] < start_of_month)]
        prev_month_spent = prev_month_expenses['amount'].sum() if not prev_month_expenses.empty else 0
        
        # Monthly comparison
        month_over_month_change = 0
        if prev_month_spent > 0:
            month_over_month_change = ((current_month_spent - prev_month_spent) / prev_month_spent) * 100
        
        # Spending by category (current month)
        category_spending = current_month_expenses.groupby('category_name')['amount'].sum().reset_index()
        category_spending = category_spending.sort_values('amount', ascending=False)
        top_categories = category_spending.head(5).to_dict('records')
        
        # Transactions by day of week
        df['day_of_week'] = df['date'].dt.day_name()
        day_spending = expenses_df.groupby('day_of_week')['amount'].sum().reset_index()
        
        # Day of week order
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_spending['day_order'] = day_spending['day_of_week'].map(lambda x: day_order.index(x))
        day_spending = day_spending.sort_values('day_order')
        day_spending = day_spending.drop('day_order', axis=1)
        
        # Average transaction amount
        avg_transaction = expenses_df['amount'].mean()
        
        # Daily average spending
        days_with_transactions = expenses_df['date'].dt.date.nunique()
        daily_avg = total_spent / days_with_transactions if days_with_transactions > 0 else 0
        
        # Recent unusual transactions
        # Calculate Z-score for transaction amounts
        mean_amount = expenses_df['amount'].mean()
        std_amount = expenses_df['amount'].std()
        
        if std_amount > 0:
            recent_expenses = expenses_df[expenses_df['date'] >= (today - timedelta(days=30))]
            recent_expenses['z_score'] = (recent_expenses['amount'] - mean_amount) / std_amount
            unusual_transactions = recent_expenses[recent_expenses['z_score'] > 2].sort_values('amount', ascending=False)
            unusual_transactions = unusual_transactions.head(5)
            unusual_list = unusual_transactions[['description', 'amount', 'date']].to_dict('records')
        else:
            unusual_list = []
        
        # Create results dictionary
        results = {
            'total_spent': float(total_spent),
            'total_income': float(total_income),
            'current_month_spent': float(current_month_spent),
            'prev_month_spent': float(prev_month_spent),
            'month_over_month_change': float(month_over_month_change),
            'top_spending_categories': top_categories,
            'day_of_week_spending': day_spending.to_dict('records'),
            'avg_transaction_amount': float(avg_transaction),
            'daily_avg_spending': float(daily_avg),
            'unusual_transactions': unusual_list
        }
        
        return results
    except Exception as e:
        logger.error(f"Error analyzing transactions: {str(e)}", exc_info=True)
        return {
            'error': str(e),
            'total_spent': 0,
            'total_income': 0,
            'current_month_spent': 0,
            'prev_month_spent': 0,
            'month_over_month_change': 0,
            'top_spending_categories': [],
            'day_of_week_spending': [],
            'avg_transaction_amount': 0,
            'daily_avg_spending': 0,
            'unusual_transactions': []
        }
