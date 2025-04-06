#!/bin/bash
# Initialization script for FinAssistant

# Set up environment variables
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
FLASK_APP=main.py
FLASK_ENV=development
SESSION_SECRET=$(python -c "import secrets; print(secrets.token_hex(24))")
DATABASE_URL=postgresql://\${PGUSER}:\${PGPASSWORD}@\${PGHOST}:\${PGPORT}/\${PGDATABASE}
EOF
    echo "Created .env file. Please update with your database credentials and API keys."
fi

# Check if Python venv is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Please activate your Python virtual environment first."
    echo "Run: python -m venv venv && source venv/bin/activate (or venv\\Scripts\\activate on Windows)"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "Initializing database tables..."
python -c "from app import app, db; app.app_context().push(); db.create_all()"

echo "Setup complete! You can now run the application with: python main.py"