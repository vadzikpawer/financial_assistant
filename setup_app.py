#!/usr/bin/env python3
"""
FinAssistant setup script.
Run this script to set up your environment before first use.
"""
import os
import secrets
import sys
from pathlib import Path


def create_env_file():
    """Create a .env file with default settings if it doesn't exist"""
    env_path = Path(".env")
    if env_path.exists():
        print("A .env file already exists. Skipping creation.")
        return

    print("Creating .env file with default settings...")

    env_content = f"""FLASK_APP=main.py
FLASK_ENV=development
SESSION_SECRET={secrets.token_hex(24)}
# Update these with your database credentials
DATABASE_URL=postgresql://postgres:password@localhost:5432/finassistant
PGUSER=postgres
PGPASSWORD=password
PGDATABASE=finassistant
PGHOST=localhost
PGPORT=5432
# Add your API keys below
# AIML_API_KEY=your_aiml_api_key
# OPENAI_API_KEY=your_openai_api_key
# DEEPSEEK_API_KEY=your_deepseek_api_key
"""

    with open(env_path, "w") as f:
        f.write(env_content)

    print(f"Created .env file at {env_path.absolute()}")
    print("Please update it with your database credentials and API keys.")


def check_virtual_env():
    """Check if running inside a virtual environment"""
    in_venv = hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )

    if not in_venv:
        print("WARNING: You are not running in a virtual environment.")
        print("It's recommended to create and activate a virtual environment first:")
        print("  python -m venv venv")
        print("  source venv/bin/activate  # On Linux/Mac")
        print("  venv\\Scripts\\activate    # On Windows")

        response = input("Continue anyway? (y/n): ")
        if response.lower() != "y":
            sys.exit(1)


def main():
    """Main setup function"""
    print("Starting FinAssistant setup...")

    check_virtual_env()
    create_env_file()

    print("\nSetup completed!")
    print("\nNext steps:")
    print("1. Install dependencies:   pip install -r requirements.txt")
    print("2. Start the application:  python main.py")
    print("3. Visit in your browser:  http://localhost:5000")


if __name__ == "__main__":
    main()
