import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_login import LoginManager
import locale

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Set locale for number formatting
try:
    locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")
except:
    locale.setlocale(locale.LC_ALL, "")


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_proto=1, x_host=1
)  # needed for url_for to generate with https

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///finance_assistant.db"
)
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"


# Add Jinja2 format_number filter
@app.template_filter("format_number")
def format_number(value):
    """Format a number with thousands separator"""
    try:
        return locale.format_string("%d", int(value), grouping=True)
    except (ValueError, TypeError):
        return value


with app.app_context():
    # Import models
    from models import (
        User,
        BankAccount,
        Transaction,
        Category,
        Recommendation,
        SavingsGoal,
    )

    # Create database tables
    db.create_all()

    # Initialize categories
    from services.transaction_analyzer import init_categories

    init_categories()

    # Import and register blueprints
    from routers.auth import auth_bp
    from routers.dashboard import dashboard_bp
    from routers.transactions import transactions_bp
    from routers.banks import banks_bp
    from routers.savings import savings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(banks_bp)
    app.register_blueprint(savings_bp)

    # User loader for flask_login
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))
