import json
import os
import logging
from datetime import datetime, timedelta
from app import db
from models import Transaction, BankAccount, Category, Recommendation
import pandas as pd

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
from openai import OpenAI

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

def generate_ai_recommendations(user_id):
    """
    Generate AI-powered personalized financial recommendations
    
    Args:
        user_id (int): User ID
        
    Returns:
        int: Number of recommendations generated
    """
    try:
        # Delete old recommendations
        old_recommendations = Recommendation.query.filter_by(user_id=user_id).all()
        for rec in old_recommendations:
            db.session.delete(rec)
        db.session.commit()
        
        # Get user's transactions
        transactions = (Transaction.query
                       .join(BankAccount)
                       .filter(BankAccount.user_id == user_id)
                       .all())
        
        # Get categories
        categories = {c.id: c for c in Category.query.all()}
        
        if not transactions:
            # No transactions, create a basic recommendation
            new_recommendation = Recommendation(
                user_id=user_id,
                title="Начните отслеживать свои расходы",
                description="Подключите банковские счета, чтобы получать детальный анализ ваших расходов и персонализированные рекомендации по экономии.",
                potential_savings=0.0
            )
            db.session.add(new_recommendation)
            db.session.commit()
            return 1
        
        # Convert to DataFrame for analysis
        transactions_data = [{
            'id': t.id,
            'amount': t.amount,
            'date': t.transaction_date,
            'description': t.description,
            'merchant': t.merchant,
            'category_id': t.category_id,
            'category_name': categories.get(t.category_id).name if t.category_id and t.category_id in categories else "Unknown",
            'is_expense': t.is_expense,
            'account_id': t.account_id
        } for t in transactions]
        
        df = pd.DataFrame(transactions_data)
        
        # Calculate some basic statistics to provide to the model
        stats = {}
        
        # Overall spending
        stats["total_spent"] = float(df[df['is_expense'] == True]['amount'].sum())
        stats["total_income"] = float(df[df['is_expense'] == False]['amount'].sum())
        
        # Monthly calculations
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month = (current_month - timedelta(days=1)).replace(day=1)
        
        current_month_expenses = df[(df['is_expense'] == True) & (df['date'] >= current_month)]
        prev_month_expenses = df[(df['is_expense'] == True) & 
                                 (df['date'] >= prev_month) & 
                                 (df['date'] < current_month)]
        
        stats["current_month_spent"] = float(current_month_expenses['amount'].sum() if not current_month_expenses.empty else 0)
        stats["prev_month_spent"] = float(prev_month_expenses['amount'].sum() if not prev_month_expenses.empty else 0)
        
        # Category spending
        category_spending = {}
        expenses_df = df[df['is_expense'] == True]
        if not expenses_df.empty and 'category_name' in expenses_df.columns:
            for category_name, group in expenses_df.groupby('category_name'):
                category_spending[category_name] = float(group['amount'].sum())
        
        stats["category_spending"] = category_spending
        
        # Create JSON for OpenAI
        data_for_ai = {
            "transactions_count": len(transactions),
            "date_range": {
                "start": df['date'].min().strftime('%Y-%m-%d') if not df.empty else "N/A",
                "end": df['date'].max().strftime('%Y-%m-%d') if not df.empty else "N/A"
            },
            "financial_stats": stats
        }
        
        # Generate AI recommendations
        ai_recommendations = get_recommendations_from_openai(data_for_ai)
        
        # Process and save recommendations
        for rec in ai_recommendations:
            # Find appropriate category if mentioned
            category_id = None
            for cat_id, cat_obj in categories.items():
                if cat_obj.name.lower() in rec["title"].lower() or cat_obj.name.lower() in rec["description"].lower():
                    category_id = cat_id
                    break
            
            # Create recommendation
            new_recommendation = Recommendation(
                user_id=user_id,
                title=rec["title"],
                description=rec["description"],
                potential_savings=float(rec["potential_savings"]),
                category_id=category_id
            )
            db.session.add(new_recommendation)
        
        db.session.commit()
        return len(ai_recommendations)
    
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {str(e)}", exc_info=True)
        db.session.rollback()
        
        # Add a fallback recommendation
        try:
            fallback_rec = Recommendation(
                user_id=user_id,
                title="Советы по экономии денег",
                description="Регулярно анализируйте свои расходы, сократите ненужные подписки и старайтесь готовить дома чаще. Эти простые шаги могут помочь вам сэкономить до 15% ваших ежемесячных расходов.",
                potential_savings=0.0
            )
            db.session.add(fallback_rec)
            db.session.commit()
            return 1
        except:
            logger.error("Failed to add fallback recommendation")
            return 0

def get_recommendations_from_openai(financial_data):
    """
    Use OpenAI to generate personalized recommendations
    
    Args:
        financial_data (dict): Dictionary with financial stats
        
    Returns:
        list: List of recommendation dictionaries
    """
    try:
        system_prompt = """
        Ты - персональный финансовый аналитик, который помогает людям экономить деньги и улучшать их финансовое положение.
        Основываясь на предоставленных данных о транзакциях и расходах, создай 3-5 полезных, конкретных и actionable рекомендаций.
        
        Правила:
        1. Рекомендации должны быть на русском языке
        2. Каждая рекомендация должна содержать title (короткий заголовок), description (развернутое описание) и potential_savings (предполагаемая экономия в рублях в месяц)
        3. Рекомендации должны быть реалистичными и основаны на данных
        4. Избегай общих советов - давай конкретные рекомендации, основанные на категориях расходов пользователя
        5. Всегда включай потенциальную экономию в рублях для каждой рекомендации
        6. Пиши в понятной и доброжелательной манере
        
        Ответ должен быть в формате JSON и содержать только массив рекомендаций:
        [
            {
                "title": "Короткий заголовок рекомендации",
                "description": "Подробное описание рекомендации с конкретными шагами",
                "potential_savings": 1000.0 // Потенциальная экономия в рублях в месяц
            },
            // другие рекомендации...
        ]
        """
        
        user_prompt = f"""
        Данные о финансах пользователя:
        
        {json.dumps(financial_data, indent=2, ensure_ascii=False)}
        
        На основе этих данных, предложи 3-5 персонализированных рекомендаций для улучшения финансового состояния.
        """
        
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        # Handle different formats that might be returned
        if isinstance(result, dict) and "recommendations" in result:
            return result["recommendations"]
        elif isinstance(result, list):
            return result
        else:
            logger.error(f"Unexpected format from OpenAI: {result}")
            return []
            
    except Exception as e:
        logger.error(f"Error getting recommendations from OpenAI: {str(e)}", exc_info=True)
        # Return basic recommendations if OpenAI fails
        return [
            {
                "title": "Оптимизируйте ежемесячные расходы",
                "description": "Проанализируйте регулярные платежи и подписки. Отмените сервисы, которыми вы редко пользуетесь, и рассмотрите возможность перехода на более выгодные тарифы для необходимых услуг.",
                "potential_savings": 1000.0
            },
            {
                "title": "Составьте бюджет на продукты",
                "description": "Планируйте покупки продуктов заранее, составляйте списки и не ходите в магазин голодными. Это поможет избежать импульсивных покупок и сэкономить на продуктах питания.",
                "potential_savings": 2000.0
            }
        ]