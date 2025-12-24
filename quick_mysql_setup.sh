#!/bin/bash

# Quick MySQL Setup Script for Telegram Bot
# This script quickly sets up MySQL with default credentials

echo "=================================================="
echo "        Quick MySQL Setup - Telegram Bot         "
echo "=================================================="
echo ""

# Check if MySQL is installed
if ! command -v mysql &> /dev/null; then
    echo "❌ MySQL is not installed!"
    echo "Installing MySQL..."
    sudo apt update
    sudo apt install mysql-server -y
fi

echo "✅ MySQL is installed"
echo ""

# Default credentials
DB_NAME="telegram_bot"
DB_USER="tunbot"
DB_PASS="TunBot@2025"

echo "🔧 Setting up database with default credentials:"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Password: $DB_PASS"
echo ""

# Run MySQL commands
sudo mysql <<EOF
CREATE DATABASE IF NOT EXISTS $DB_NAME;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Database setup successful!"
    
    # Update .env file
    echo ""
    echo "📝 Updating .env file..."
    
    # Create or update .env
    if [ ! -f .env ]; then
        cp .env.example .env 2>/dev/null || touch .env
    fi
    
    # Remove old MySQL entries
    sed -i '/^MYSQL_/d' .env
    
    # Add new MySQL entries
    cat >> .env <<ENVEOF

# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_USER=$DB_USER
MYSQL_PASSWORD=$DB_PASS
MYSQL_DATABASE=$DB_NAME
MYSQL_PORT=3306
ENVEOF
    
    echo "✅ .env file updated!"
    echo ""
    echo "=================================================="
    echo "           Setup Complete! ✅                     "
    echo "=================================================="
    echo ""
    echo "Your database credentials:"
    echo "  User: $DB_USER"
    echo "  Password: $DB_PASS"
    echo "  Database: $DB_NAME"
    echo ""
    echo "Test the connection:"
    echo "  python3 test_db.py"
    echo ""
    echo "Run the bot:"
    echo "  python3 telegram_bot.py"
    echo ""
else
    echo "❌ Failed to setup database"
    echo ""
    echo "Please run these commands manually:"
    echo "  sudo mysql"
    echo "  CREATE DATABASE IF NOT EXISTS $DB_NAME;"
    echo "  CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';"
    echo "  GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';"
    echo "  FLUSH PRIVILEGES;"
    echo "  exit"
fi
