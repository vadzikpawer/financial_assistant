import json
import os
import logging
from datetime import datetime, timedelta
from app import db
from models import Transaction, BankAccount, Category, Recommendation
import pandas as pd
import requests
from deepseek_ai import DeepSeekAI  # Import DeepSeek AI library
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# DeepSeek configuration
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

# Global flag to track API status
ai_api_active = True
deepseek_client = None

# Initialize DeepSeek client
if DEEPSEEK_API_KEY:
    try:
        # Initialize DeepSeek AI client with the API key
        deepseek_client = DeepSeekAI(
            api_key=DEEPSEEK_API_KEY
        )
        logger.info("DeepSeek AI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize DeepSeek client: {str(e)}")
        ai_api_active = False
else:
    logger.warning("No DeepSeek API key found. AI recommendations will be disabled.")
    ai_api_active = False

def generate_ai_recommendations(user_id):
    """
    Generate AI-powered personalized financial recommendations
    
    Args:
        user_id (int): User ID
        
    Returns:
        tuple: (recommendations_count, using_ai_flag)
    """
    global ai_api_active
    using_ai = False
    
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
            return 1, False
        
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
        
        # Create JSON for AI
        data_for_ai = {
            "transactions_count": len(transactions),
            "date_range": {
                "start": df['date'].min().strftime('%Y-%m-%d') if not df.empty else "N/A",
                "end": df['date'].max().strftime('%Y-%m-%d') if not df.empty else "N/A"
            },
            "financial_stats": stats
        }
        
        # Check if DeepSeek API is available before making the call
        if ai_api_active and deepseek_client:
            logger.info("Using DeepSeek AI for recommendations")
            using_ai = True
        else:
            logger.info("Using rule-based recommendations (DeepSeek API not available)")
            using_ai = False
        
        # Generate recommendations
        ai_recommendations = get_recommendations_from_deepseek(data_for_ai)
        
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
        return len(ai_recommendations), using_ai
    
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
            return 1, False
        except:
            logger.error("Failed to add fallback recommendation")
            return 0, False

def get_recommendations_from_deepseek(financial_data):
    """
    Use DeepSeek AI to generate personalized recommendations
    
    Args:
        financial_data (dict): Dictionary with financial stats
        
    Returns:
        list: List of recommendation dictionaries
    """
    global ai_api_active, deepseek_client
    
    # Check if DeepSeek API is active and properly configured
    if not ai_api_active or not deepseek_client:
        logger.warning("DeepSeek API is not active or not configured. Using rule-based recommendations.")
        return get_rule_based_recommendations(financial_data)
    
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
        
        # Call DeepSeek API
        # The chat object is not callable, we need to use the create method
        response = deepseek_client.chat.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Extract result text
        result_text = response.choices[0].message.content
        
        # Try to parse JSON from response
        try:
            # Find JSON in response (sometimes it might be within a markdown code block)
            if "```json" in result_text:
                json_start = result_text.find("```json") + 7
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
            elif "```" in result_text:
                json_start = result_text.find("```") + 3
                json_end = result_text.find("```", json_start)
                result_text = result_text[json_start:json_end].strip()
                
            # Parse the JSON
            result = json.loads(result_text)
            
            # Handle different formats that might be returned
            if isinstance(result, dict) and "recommendations" in result:
                return result["recommendations"]
            elif isinstance(result, list):
                return result
            else:
                logger.error(f"Unexpected format from DeepSeek: {result}")
                return get_rule_based_recommendations(financial_data)
        except json.JSONDecodeError:
            logger.error("Failed to parse JSON from DeepSeek response")
            logger.debug(f"DeepSeek response: {result_text}")
            return get_rule_based_recommendations(financial_data)
            
    except requests.exceptions.RequestException as e:
        logger.error(f"DeepSeek API error: {str(e)}")
        # Set the global flag to indicate API is not available
        ai_api_active = False
        # Return rule-based recommendations
        return get_rule_based_recommendations(financial_data, api_error=True)
        
    except Exception as e:
        logger.error(f"Error getting recommendations from DeepSeek: {str(e)}", exc_info=True)
        # Return rule-based recommendations
        return get_rule_based_recommendations(financial_data)

def get_rule_based_recommendations(financial_data, quota_exceeded=False, api_error=False):
    """
    Generate rule-based recommendations when the AI API is unavailable
    
    Args:
        financial_data (dict): Dictionary with financial stats
        quota_exceeded (bool): Whether the quota was exceeded
        api_error (bool): Whether there was an API error
        
    Returns:
        list: List of recommendation dictionaries
    """
    recommendations = []
    
    # Add notification about API issues if needed
    if quota_exceeded:
        recommendations.append({
            "title": "Уведомление о сервисе рекомендаций",
            "description": "В данный момент сервис AI-рекомендаций временно недоступен из-за превышения лимита API запросов. Мы предоставляем базовые рекомендации по экономии. Пожалуйста, попробуйте обновить рекомендации позже.",
            "potential_savings": 0.0
        })
    elif api_error:
        recommendations.append({
            "title": "Уведомление о сервисе рекомендаций",
            "description": "В данный момент сервис AI-рекомендаций временно недоступен из-за технических проблем. Мы предоставляем базовые рекомендации по экономии. Пожалуйста, попробуйте обновить рекомендации позже.",
            "potential_savings": 0.0
        })
    
    # Basic recommendations that are generally useful
    basic_recommendations = [
        {
            "title": "Оптимизируйте ежемесячные расходы",
            "description": "Проанализируйте регулярные платежи и подписки. Отмените сервисы, которыми вы редко пользуетесь, и рассмотрите возможность перехода на более выгодные тарифы для необходимых услуг.",
            "potential_savings": 1000.0
        },
        {
            "title": "Составьте бюджет на продукты",
            "description": "Планируйте покупки продуктов заранее, составляйте списки и не ходите в магазин голодными. Это поможет избежать импульсивных покупок и сэкономить на продуктах питания.",
            "potential_savings": 2000.0
        },
        {
            "title": "Сократите расходы на доставку еды",
            "description": "Доставка еды обычно стоит на 30-50% дороже, чем приготовление пищи дома. Попробуйте готовить большие порции на несколько дней вперед, чтобы сэкономить время и деньги.",
            "potential_savings": 3000.0
        },
        {
            "title": "Откладывайте 10% дохода",
            "description": "Попробуйте автоматически откладывать 10% от всех доходов в день получения зарплаты. Создайте отдельный сберегательный счет для этой цели и настройте автоматические переводы.",
            "potential_savings": 5000.0
        },
        {
            "title": "Используйте кэшбэк и бонусные программы",
            "description": "Подключите банковские карты с кэшбэком и используйте программы лояльности в магазинах, где вы регулярно совершаете покупки. Это позволит вам вернуть часть ваших расходов.",
            "potential_savings": 1500.0
        }
    ]
    
    # Add data-driven recommendations if we have financial data
    if financial_data and "financial_stats" in financial_data:
        stats = financial_data["financial_stats"]
        
        # If we have category spending data, generate more specific recommendations
        if "category_spending" in stats and stats["category_spending"]:
            category_spending = stats["category_spending"]
            
            # Find the top spending categories
            sorted_categories = sorted(category_spending.items(), key=lambda x: x[1], reverse=True)
            
            if sorted_categories:
                # Generate recommendations for top 2 categories
                for idx, (category, amount) in enumerate(sorted_categories[:2]):
                    saving_percent = 0.15  # 15% savings goal
                    potential_savings = round(amount * saving_percent)
                    
                    if idx == 0:  # First category (highest spending)
                        recommendations.append({
                            "title": f"Сократите расходы на категорию '{category}'",
                            "description": f"Это ваша самая большая категория расходов - {int(amount)} ₽. Рассмотрите способы сократить эти траты на 15-20%, например, сравнивайте цены перед покупкой или ищите альтернативные решения.",
                            "potential_savings": potential_savings
                        })
                    else:  # Second category
                        recommendations.append({
                            "title": f"Оптимизируйте расходы в категории '{category}'",
                            "description": f"Вы тратите значительную сумму ({int(amount)} ₽) на '{category}'. Подумайте, как можно оптимизировать эти расходы, например, искать скидки, акции или более выгодные предложения.",
                            "potential_savings": potential_savings
                        })
                        
        # If we have monthly spending data, compare current month with previous
        if "current_month_spent" in stats and "prev_month_spent" in stats:
            current = stats["current_month_spent"]
            previous = stats["prev_month_spent"]
            
            if previous > 0 and current > previous * 1.15:  # Spending increased by more than 15%
                recommendations.append({
                    "title": "Контролируйте рост расходов",
                    "description": f"В текущем месяце ваши расходы ({int(current)} ₽) превышают расходы предыдущего месяца ({int(previous)} ₽) на {int((current/previous - 1) * 100)}%. Проанализируйте, в каких категориях выросли расходы, и попробуйте их сократить.",
                    "potential_savings": round((current - previous) * 0.5)  # 50% of the increase
                })
    
    # Combine recommendations
    if recommendations:
        # Add some basic recommendations if we don't have enough
        remaining_slots = 3 - len(recommendations)
        if remaining_slots > 0:
            recommendations.extend(basic_recommendations[:remaining_slots])
    else:
        # Use basic recommendations if we couldn't generate any
        recommendations = basic_recommendations[:3]
    
    return recommendations