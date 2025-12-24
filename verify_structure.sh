#!/bin/bash

echo "🔍 بررسی ساختار پروژه..."
echo ""

echo "📁 پوشه فعلی:"
pwd
echo ""

echo "📂 فایل‌های موجود:"
ls -la
echo ""

echo "📂 محتویات handlers/:"
if [ -d "handlers" ]; then
    ls -la handlers/
else
    echo "❌ پوشه handlers وجود ندارد!"
fi
echo ""

echo "📂 محتویات utils/:"
if [ -d "utils" ]; then
    ls -la utils/
else
    echo "❌ پوشه utils وجود ندارد!"
fi
echo ""

echo "🐍 نسخه Python:"
python3 --version
echo ""

echo "📦 بسته‌های نصب شده:"
pip3 list | grep -i telegram
echo ""

echo "🧪 تست import ها:"
python3 test_imports.py
