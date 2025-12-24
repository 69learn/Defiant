#!/bin/bash

# Telegram Bot Runner
# این فایل PYTHONPATH را تنظیم کرده و ربات را اجرا میکند

cd "$(dirname "$0")"

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "🤖 در حال راه‌اندازی Telegram Bot..."
echo "📁 Directory: $(pwd)"
echo "🐍 Python Path: $PYTHONPATH"
echo ""

python3 telegram_bot.py
