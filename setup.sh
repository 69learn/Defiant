#!/bin/bash

echo "🚀 نصب Telegram Bot"
echo "===================="

# بررسی Python
if ! command -v python3 &> /dev/null; then
    echo "نصب Python3..."
    apt-get update
    apt-get install -y python3 python3-pip
fi

# بررسی MySQL
if ! command -v mysql &> /dev/null; then
    echo "نصب MySQL..."
    apt-get install -y mysql-server
fi

# ایجاد فایل .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ فایل .env ایجاد شد. لطفاً آن را تدوین کنید."
fi

# نصب وابستگی‌های Python
echo "نصب وابستگی‌ها..."
pip3 install -r requirements.txt

# ایجاد دیتابیس MySQL
echo "ایجاد دیتابیس..."
mysql -u root -e "CREATE DATABASE IF NOT EXISTS telegram_bot;"

echo "✅ نصب کامل شد!"
echo ""
echo "برای شروع ربات:"
echo "python3 telegram_bot.py"
