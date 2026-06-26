#!/bin/bash

echo "🚀 Setting up PPE Detection System with Database and Notifications..."

# Install new dependencies
echo "📦 Installing new dependencies..."
pip install sqlalchemy alembic passlib[bcrypt] python-jose[cryptography] python-multipart email-validator aiosmtplib httpx schedule pytz

# Create database directory if it doesn't exist
mkdir -p data

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from app.database import init_db; init_db(); print('Database initialized successfully!')"

# Check if .env file needs updating
echo "📝 Checking environment configuration..."
if ! grep -q "DATABASE_URL" .env; then
    echo "⚠️  Your .env file needs updating. Please configure email and webhook settings."
    echo "✅ Setup complete! Please update your .env file with notification settings."
else
    echo "✅ Setup complete!"
fi

echo ""
echo "🎉 PPE Detection System is ready!"
echo ""
echo "📋 Next steps:"
echo "1. Update .env file with your email and webhook settings"
echo "2. Run: source .venv/bin/activate"
echo "3. Run: python -m uvicorn app.main:app --reload"
echo "4. Open: http://localhost:8000/dashboard"
echo ""
echo "🔧 New features available:"
echo "- Database persistence for detections"
echo "- Email notifications for violations"
echo "- Webhook integrations"
echo "- Historical statistics"
echo "- Data export functionality"
echo "- Daily summary reports"