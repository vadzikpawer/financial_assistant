import httpx
import logging
import json
from datetime import datetime, timedelta
from app import db
from models import Transaction
from services.transaction_analyzer import categorize_transaction

logger = logging.getLogger(__name__)

# Constants
TINKOFF_API_URL = "https://api.tinkoff.ru/v1"
SBER_API_URL = "https://api.sberbank.ru/v1"

# Mock banks for development (in real app, this would be from a database)
SUPPORTED_BANKS = [
    {"id": "tinkoff", "name": "Тинькофф Банк", "logo": "tinkoff.svg"},
    {"id": "sber", "name": "Сбербанк", "logo": "sber.svg"},
    {"id": "vtb", "name": "ВТБ", "logo": "vtb.svg"},
    {"id": "alpha", "name": "Альфа-Банк", "logo": "alpha.svg"},
    {"id": "gazprombank", "name": "Газпромбанк", "logo": "gazprombank.svg"}
]

def get_supported_banks():
    """Return list of supported banks"""
    return SUPPORTED_BANKS

def connect_to_bank(bank_name, credentials):
    """
    Connect to a bank's API using provided credentials
    
    Args:
        bank_name (str): Name of the bank
        credentials (dict): Authentication credentials
        
    Returns:
        str: Access token if successful, None otherwise
    """
    try:
        if bank_name.lower() == "tinkoff":
            return connect_to_tinkoff(credentials)
        elif bank_name.lower() == "sber":
            return connect_to_sber(credentials)
        elif bank_name.lower() in ["vtb", "alpha", "gazprombank"]:
            # For demo purposes, simulate connection to other banks
            logger.debug(f"Simulating connection to {bank_name}")
            # In a real app, we would make an actual API call here
            return f"demo_token_{bank_name}_{datetime.utcnow().timestamp()}"
        else:
            logger.error(f"Unsupported bank: {bank_name}")
            return None
    except Exception as e:
        logger.error(f"Error connecting to {bank_name}: {str(e)}")
        return None

def connect_to_tinkoff(credentials):
    """Connect to Tinkoff Bank API"""
    try:
        # In a real app, this would make an actual API call to Tinkoff
        # For demo purposes, simulate a successful connection
        logger.debug("Connecting to Tinkoff Bank API")
        
        # In a real app, we would use:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{TINKOFF_API_URL}/auth",
        #         json=credentials
        #     )
        #     response.raise_for_status()
        #     return response.json()["accessToken"]
        
        return f"tinkoff_demo_token_{datetime.utcnow().timestamp()}"
    except Exception as e:
        logger.error(f"Error connecting to Tinkoff: {str(e)}")
        raise

def connect_to_sber(credentials):
    """Connect to Sberbank API"""
    try:
        # In a real app, this would make an actual API call to Sberbank
        # For demo purposes, simulate a successful connection
        logger.debug("Connecting to Sberbank API")
        
        # In a real app, we would use:
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{SBER_API_URL}/auth",
        #         json=credentials
        #     )
        #     response.raise_for_status()
        #     return response.json()["accessToken"]
        
        return f"sber_demo_token_{datetime.utcnow().timestamp()}"
    except Exception as e:
        logger.error(f"Error connecting to Sberbank: {str(e)}")
        raise

def fetch_account_data(bank_name, access_token):
    """
    Fetch account information from bank
    
    Args:
        bank_name (str): Name of the bank
        access_token (str): Authentication token
        
    Returns:
        list: List of account information dictionaries
    """
    try:
        if bank_name.lower() == "tinkoff":
            return fetch_tinkoff_accounts(access_token)
        elif bank_name.lower() == "sber":
            return fetch_sber_accounts(access_token)
        elif bank_name.lower() in ["vtb", "alpha", "gazprombank"]:
            # For demo purposes, simulate accounts for other banks
            logger.debug(f"Simulating account fetch for {bank_name}")
            
            # Generate sample accounts
            return [
                {
                    "account_number": f"{bank_name}_debit_{datetime.utcnow().timestamp()}",
                    "account_type": "Дебетовая карта",
                    "balance": 45000.0,
                    "currency": "RUB"
                },
                {
                    "account_number": f"{bank_name}_credit_{datetime.utcnow().timestamp()}",
                    "account_type": "Кредитная карта",
                    "balance": 75000.0,
                    "currency": "RUB"
                }
            ]
        else:
            logger.error(f"Unsupported bank: {bank_name}")
            return []
    except Exception as e:
        logger.error(f"Error fetching accounts from {bank_name}: {str(e)}")
        raise

def fetch_tinkoff_accounts(access_token):
    """Fetch account information from Tinkoff Bank"""
    try:
        # In a real app, this would make an actual API call to Tinkoff
        # For demo purposes, simulate account data
        logger.debug("Fetching Tinkoff accounts")
        
        # In a real app, we would use:
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(
        #         f"{TINKOFF_API_URL}/accounts",
        #         headers={"Authorization": f"Bearer {access_token}"}
        #     )
        #     response.raise_for_status()
        #     return [
        #         {
        #             "account_number": acc["accountNumber"],
        #             "account_type": acc["accountType"],
        #             "balance": acc["balance"],
        #             "currency": acc["currency"]
        #         }
        #         for acc in response.json()["accounts"]
        #     ]
        
        # Return demo accounts
        return [
            {
                "account_number": f"tinkoff_black_{datetime.utcnow().timestamp()}",
                "account_type": "Дебетовая карта Tinkoff Black",
                "balance": 135750.25,
                "currency": "RUB"
            },
            {
                "account_number": f"tinkoff_platinum_{datetime.utcnow().timestamp()}",
                "account_type": "Кредитная карта Tinkoff Platinum",
                "balance": 50000.0,
                "currency": "RUB"
            }
        ]
    except Exception as e:
        logger.error(f"Error fetching Tinkoff accounts: {str(e)}")
        raise

def fetch_sber_accounts(access_token):
    """Fetch account information from Sberbank"""
    try:
        # In a real app, this would make an actual API call to Sberbank
        # For demo purposes, simulate account data
        logger.debug("Fetching Sberbank accounts")
        
        # In a real app, we would use:
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(
        #         f"{SBER_API_URL}/accounts",
        #         headers={"Authorization": f"Bearer {access_token}"}
        #     )
        #     response.raise_for_status()
        #     return [
        #         {
        #             "account_number": acc["accountNumber"],
        #             "account_type": acc["accountType"],
        #             "balance": acc["balance"],
        #             "currency": acc["currency"]
        #         }
        #         for acc in response.json()["accounts"]
        #     ]
        
        # Return demo accounts
        return [
            {
                "account_number": f"sber_debit_{datetime.utcnow().timestamp()}",
                "account_type": "Дебетовая карта СберКарта",
                "balance": 87500.0,
                "currency": "RUB"
            },
            {
                "account_number": f"sber_savings_{datetime.utcnow().timestamp()}",
                "account_type": "Сберегательный счёт",
                "balance": 250000.0,
                "currency": "RUB"
            }
        ]
    except Exception as e:
        logger.error(f"Error fetching Sberbank accounts: {str(e)}")
        raise

def fetch_transactions(bank_name, access_token, account_number, days=30):
    """
    Fetch transaction history for an account
    
    Args:
        bank_name (str): Name of the bank
        access_token (str): Authentication token
        account_number (str): Account number
        days (int): Number of days of history to fetch
        
    Returns:
        list: List of transaction dictionaries
    """
    try:
        if bank_name.lower() == "tinkoff":
            return fetch_tinkoff_transactions(access_token, account_number, days)
        elif bank_name.lower() == "sber":
            return fetch_sber_transactions(access_token, account_number, days)
        elif bank_name.lower() in ["vtb", "alpha", "gazprombank"]:
            # For demo purposes, generate transactions for other banks
            logger.debug(f"Simulating transactions for {bank_name} account {account_number}")
            
            # Generate sample transactions
            return generate_sample_transactions(bank_name, account_number, days)
        else:
            logger.error(f"Unsupported bank: {bank_name}")
            return []
    except Exception as e:
        logger.error(f"Error fetching transactions from {bank_name}: {str(e)}")
        raise

def fetch_tinkoff_transactions(access_token, account_number, days=30):
    """Fetch transaction history from Tinkoff Bank"""
    try:
        # In a real app, this would make an actual API call to Tinkoff
        # For demo purposes, generate sample transactions
        logger.debug(f"Fetching Tinkoff transactions for account {account_number}")
        
        # In a real app, we would use:
        # from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(
        #         f"{TINKOFF_API_URL}/accounts/{account_number}/transactions",
        #         headers={"Authorization": f"Bearer {access_token}"},
        #         params={"from": from_date}
        #     )
        #     response.raise_for_status()
        #     return [
        #         {
        #             "external_id": tx["id"],
        #             "amount": tx["amount"],
        #             "currency": tx["currency"],
        #             "description": tx["description"],
        #             "date": datetime.fromisoformat(tx["date"]),
        #             "merchant": tx.get("merchant", {}).get("name", "")
        #         }
        #         for tx in response.json()["transactions"]
        #     ]
        
        # Return demo transactions
        return generate_sample_transactions("tinkoff", account_number, days)
    except Exception as e:
        logger.error(f"Error fetching Tinkoff transactions: {str(e)}")
        raise

def fetch_sber_transactions(access_token, account_number, days=30):
    """Fetch transaction history from Sberbank"""
    try:
        # In a real app, this would make an actual API call to Sberbank
        # For demo purposes, generate sample transactions
        logger.debug(f"Fetching Sberbank transactions for account {account_number}")
        
        # In a real app, we would use:
        # from_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(
        #         f"{SBER_API_URL}/accounts/{account_number}/transactions",
        #         headers={"Authorization": f"Bearer {access_token}"},
        #         params={"from": from_date}
        #     )
        #     response.raise_for_status()
        #     return [
        #         {
        #             "external_id": tx["id"],
        #             "amount": tx["amount"],
        #             "currency": tx["currency"],
        #             "description": tx["description"],
        #             "date": datetime.fromisoformat(tx["date"]),
        #             "merchant": tx.get("merchant", "")
        #         }
        #         for tx in response.json()["transactions"]
        #     ]
        
        # Return demo transactions
        return generate_sample_transactions("sber", account_number, days)
    except Exception as e:
        logger.error(f"Error fetching Sberbank transactions: {str(e)}")
        raise

def generate_sample_transactions(bank_name, account_number, days=30):
    """Generate sample transactions for demo purposes"""
    from random import randint, choice, uniform
    
    # Common Russian merchants and transaction descriptions
    merchants = [
        "Пятёрочка", "Магнит", "OZON", "Wildberries", "Яндекс.Такси", 
        "Dodo Пицца", "Лента", "Перекрёсток", "М.Видео", "Starbucks",
        "KFC", "McDonald's", "IKEA", "АЗС Газпром", "Аптека 36.6", 
        "Okko", "Детский мир", "H&M", "Zara", "DNS", "Спортмастер"
    ]
    
    transaction_types = [
        "Оплата", "Покупка", "Платеж", "Перевод", "Списание", "Снятие наличных"
    ]
    
    transactions = []
    now = datetime.utcnow()
    
    # Generate random transactions
    for i in range(50):  # Generate 50 sample transactions
        # Random date within the past 'days' days
        days_ago = randint(0, days)
        hours_ago = randint(0, 23)
        minutes_ago = randint(0, 59)
        
        date = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        
        # Random amount (mostly expenses, some income)
        is_expense = randint(0, 9) < 8  # 80% chance of expense
        
        amount = 0
        if is_expense:
            # Expenses: typically between 100 and 5000 rubles
            amount = round(uniform(100, 5000), 2)
        else:
            # Income: typically larger amounts
            amount = round(uniform(5000, 50000), 2)
            
        # For expenses, amount is negative
        if is_expense:
            amount = -amount
            
        merchant = choice(merchants) if is_expense else ""
        transaction_type = choice(transaction_types) if is_expense else "Зачисление"
        
        description = ""
        if is_expense:
            description = f"{transaction_type} {merchant}"
        else:
            description = "Зачисление средств" if randint(0, 1) == 0 else "Перевод от клиента"
            
        # Create transaction object
        transaction = {
            "external_id": f"{bank_name}_{account_number}_{i}_{date.timestamp()}",
            "amount": abs(amount),  # Store as positive number
            "currency": "RUB",
            "description": description,
            "date": date,
            "merchant": merchant if is_expense else "",
            "is_expense": is_expense
        }
        
        transactions.append(transaction)
    
    # Sort by date, newest first
    transactions.sort(key=lambda x: x["date"], reverse=True)
    
    return transactions

def sync_account_data(bank_name, access_token, account_number, account_id):
    """
    Sync account data and transactions from bank
    
    Args:
        bank_name (str): Name of the bank
        access_token (str): Authentication token
        account_number (str): Account number
        account_id (int): Database ID of the account
        
    Returns:
        tuple: (new_balance, new_transaction_count)
    """
    try:
        # Fetch latest account data (new balance)
        accounts_data = fetch_account_data(bank_name, access_token)
        
        # Find matching account
        account_data = next((a for a in accounts_data if a["account_number"] == account_number), None)
        
        if not account_data:
            logger.error(f"Account {account_number} not found in {bank_name} data")
            raise ValueError(f"Account {account_number} not found")
        
        new_balance = account_data["balance"]
        
        # Fetch latest transactions
        transactions = fetch_transactions(bank_name, access_token, account_number)
        
        # Insert new transactions
        new_transaction_count = 0
        for transaction_data in transactions:
            # Check if transaction already exists
            existing_transaction = Transaction.query.filter_by(
                external_id=transaction_data["external_id"]
            ).first()
            
            if not existing_transaction:
                # Categorize transaction
                category_id = categorize_transaction(
                    transaction_data["description"],
                    transaction_data.get("merchant", "")
                )
                
                # Create new transaction
                new_transaction = Transaction(
                    account_id=account_id,
                    external_id=transaction_data["external_id"],
                    amount=transaction_data["amount"],
                    currency=transaction_data["currency"],
                    description=transaction_data["description"],
                    transaction_date=transaction_data["date"],
                    merchant=transaction_data.get("merchant", ""),
                    category_id=category_id,
                    is_expense=transaction_data["is_expense"]
                )
                db.session.add(new_transaction)
                new_transaction_count += 1
        
        db.session.commit()
        
        return new_balance, new_transaction_count
    except Exception as e:
        logger.error(f"Error syncing account data: {str(e)}")
        raise
