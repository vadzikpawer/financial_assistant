import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from app import db
from models import Transaction, BankAccount, Category, Recommendation
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)

def generate_recommendations(user_id):
    """
    Generate money-saving recommendations based on user's transaction history
    
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
            'is_expense': t.is_expense,
            'account_id': t.account_id
        } for t in transactions]
        
        df = pd.DataFrame(transactions_data)
        
        # Get categories
        categories = {c.id: c for c in Category.query.all()}
        
        # Generate recommendations
        recommendations = []
        
        # 1. Identify high-spending categories
        if not df.empty and 'category_id' in df.columns and 'amount' in df.columns:
            expense_df = df[df['is_expense'] == True]
            
            if not expense_df.empty and 'category_id' in expense_df.columns:
                # Group by category and calculate total spending
                category_spending = expense_df.groupby('category_id')['amount'].sum().reset_index()
                category_spending = category_spending.sort_values('amount', ascending=False)
                
                # Top spending category
                if not category_spending.empty:
                    top_category_id = category_spending.iloc[0]['category_id']
                    top_category = categories.get(top_category_id)
                    
                    if top_category:
                        total_spent = category_spending.iloc[0]['amount']
                        avg_monthly = total_spent / 3  # Assume data is for about 3 months
                        potential_savings = avg_monthly * 0.15  # Suggest 15% reduction
                        
                        recommendation = Recommendation(
                            user_id=user_id,
                            title=f"Сократите расходы на {top_category.name}",
                            description=f"Вы тратите значительную часть своего бюджета на {top_category.name}. "
                                       f"Попробуйте сократить эти расходы на 15%, это позволит вам сэкономить "
                                       f"около {potential_savings:.0f} ₽ в месяц.",
                            potential_savings=potential_savings,
                            category_id=top_category_id
                        )
                        recommendations.append(recommendation)
        
        # 2. Identify subscription services
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        prev_month = (current_month - timedelta(days=1)).replace(day=1)
        two_months_ago = (prev_month - timedelta(days=1)).replace(day=1)
        
        # Find recurring transactions of similar amounts
        if not df.empty and 'date' in df.columns and 'amount' in df.columns:
            df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
            
            # Group by month and merchant, looking for similar amounts
            potential_subscriptions = []
            
            for merchant in df['merchant'].unique():
                if not merchant:
                    continue
                    
                merchant_df = df[df['merchant'] == merchant]
                monthly_charges = merchant_df.groupby('month')['amount'].sum()
                
                # Check if charges exist for at least 2 months with similar amounts
                if len(monthly_charges) >= 2:
                    amounts = monthly_charges.values
                    if np.std(amounts) / np.mean(amounts) < 0.1:  # Low variance in amounts
                        potential_subscriptions.append({
                            'merchant': merchant,
                            'amount': np.mean(amounts),
                            'count': len(monthly_charges)
                        })
            
            # Create recommendations for subscriptions
            if potential_subscriptions:
                total_subscription_cost = sum(sub['amount'] for sub in potential_subscriptions)
                
                subscription_text = "Потенциальные подписки:\n"
                for sub in potential_subscriptions:
                    subscription_text += f"- {sub['merchant']}: ~{sub['amount']:.0f} ₽/месяц\n"
                
                recommendation = Recommendation(
                    user_id=user_id,
                    title="Проверьте свои регулярные подписки",
                    description=f"Мы обнаружили несколько регулярных платежей, которые могут быть подписками. "
                               f"Проверьте, все ли из них вам действительно нужны. "
                               f"Отключение ненужных подписок может сэкономить до {total_subscription_cost:.0f} ₽ в месяц.\n\n"
                               f"{subscription_text}",
                    potential_savings=total_subscription_cost / 2  # Assume half could be cancelled
                )
                recommendations.append(recommendation)
        
        # 3. Dining out recommendation
        if not df.empty and 'category_id' in df.columns and 'amount' in df.columns:
            # Check for restaurant category
            restaurant_category = next((c for c in categories.values() if c.name == "Рестораны"), None)
            
            if restaurant_category:
                restaurant_expenses = df[(df['category_id'] == restaurant_category.id) & (df['is_expense'] == True)]
                
                if not restaurant_expenses.empty:
                    monthly_dining = restaurant_expenses['amount'].sum() / 3  # Assume 3 months of data
                    
                    if monthly_dining > 5000:  # If spending more than 5000₽ monthly on dining
                        potential_savings = monthly_dining * 0.3  # Suggest 30% reduction
                        
                        recommendation = Recommendation(
                            user_id=user_id,
                            title="Готовьте дома чаще",
                            description=f"Вы тратите около {monthly_dining:.0f} ₽ в месяц на кафе и рестораны. "
                                       f"Приготовление еды дома вместо походов в рестораны может сэкономить "
                                       f"до {potential_savings:.0f} ₽ ежемесячно.",
                            potential_savings=potential_savings,
                            category_id=restaurant_category.id
                        )
                        recommendations.append(recommendation)
        
        # 4. General savings recommendation
        total_expenses = df[df['is_expense'] == True]['amount'].sum()
        total_income = df[df['is_expense'] == False]['amount'].sum()
        
        if total_income > 0:
            savings_rate = 1 - (total_expenses / total_income)
            
            if savings_rate < 0.2:  # If saving less than 20% of income
                target_rate = 0.2
                current_monthly_income = total_income / 3  # Assume 3 months of data
                current_monthly_savings = current_monthly_income * savings_rate
                target_monthly_savings = current_monthly_income * target_rate
                additional_savings_needed = target_monthly_savings - current_monthly_savings
                
                recommendation = Recommendation(
                    user_id=user_id,
                    title="Увеличьте процент сбережений",
                    description=f"В настоящее время вы сберегаете около {savings_rate*100:.1f}% своего дохода. "
                               f"Финансовые эксперты рекомендуют сберегать не менее 20% дохода. "
                               f"Попробуйте увеличить ежемесячные сбережения на {additional_savings_needed:.0f} ₽, "
                               f"чтобы достичь рекомендуемого уровня.",
                    potential_savings=additional_savings_needed
                )
                recommendations.append(recommendation)
        
        # 5. Check for cash withdrawals
        if not df.empty and 'description' in df.columns and 'amount' in df.columns:
            cash_keywords = ["снятие", "наличные", "банкомат", "atm"]
            cash_withdrawals = df[df['description'].str.lower().str.contains('|'.join(cash_keywords), na=False)]
            
            if not cash_withdrawals.empty:
                monthly_cash = cash_withdrawals['amount'].sum() / 3  # Assume 3 months of data
                
                if monthly_cash > 10000:  # If withdrawing more than 10000₽ monthly
                    potential_savings = monthly_cash * 0.1  # Assume 10% savings from better tracking
                    
                    recommendation = Recommendation(
                        user_id=user_id,
                        title="Уменьшите использование наличных",
                        description=f"Вы снимаете около {monthly_cash:.0f} ₽ наличными каждый месяц. "
                                   f"Платежи картой легче отследить и проанализировать. "
                                   f"Уменьшение использования наличных поможет вам лучше контролировать расходы "
                                   f"и может сэкономить до {potential_savings:.0f} ₽ в месяц.",
                        potential_savings=potential_savings
                    )
                    recommendations.append(recommendation)
        
        # Add all recommendations to database
        for rec in recommendations:
            db.session.add(rec)
        
        db.session.commit()
        
        return len(recommendations)
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
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
