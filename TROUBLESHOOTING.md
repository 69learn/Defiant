# راهنمای رفع مشکلات

## خطای ModuleNotFoundError: No module named 'handlers.backhaul_handler'

این خطا زمانی رخ می‌دهد که Python نمی‌تواند ماژول handlers را پیدا کند.

### مرحله 1: بررسی ساختار پروژه

ابتدا مطمئن شوید که تمام فایل‌ها در جای درست قرار دارند:

\`\`\`bash
chmod +x verify_structure.sh
./verify_structure.sh
\`\`\`

### مرحله 2: بررسی فایل‌های موجود

ساختار صحیح پروژه باید به این شکل باشد:

\`\`\`
telegram-bot/
├── telegram_bot.py
├── config.py
├── database.py
├── requirements.txt
├── .env
├── handlers/
│   ├── __init__.py
│   ├── start_handler.py
│   ├── tunnel_handler.py
│   ├── backhaul_handler.py
│   ├── panel_handler.py
│   └── other_handler.py
└── utils/
    ├── __init__.py
    ├── ssh_manager.py
    └── tunnel_utils.py
\`\`\`

### مرحله 3: اطمینان از وجود فایل‌های __init__.py

فایل‌های `__init__.py` باید در پوشه‌های handlers و utils وجود داشته باشند:

\`\`\`bash
# ایجاد فایل __init__.py اگر وجود ندارد
touch handlers/__init__.py
touch utils/__init__.py
\`\`\`

### مرحله 4: تست import ها

\`\`\`bash
python3 test_imports.py
\`\`\`

اگر خطایی مشاهده کردید، به دقت پیام خطا را بخوانید.

### مرحله 5: بررسی وابستگی‌ها

مطمئن شوید تمام وابستگی‌ها نصب شده‌اند:

\`\`\`bash
pip3 install -r requirements.txt
\`\`\`

### مرحله 6: اجرای ربات

\`\`\`bash
chmod +x run_bot.sh
./run_bot.sh
\`\`\`

## خطاهای رایج دیگر

### خطای "No module named 'telegram'"

\`\`\`bash
pip3 install python-telegram-bot
\`\`\`

### خطای "No module named 'dotenv'"

\`\`\`bash
pip3 install python-dotenv
\`\`\`

### خطای "No module named 'pymysql'"

\`\`\`bash
pip3 install pymysql
\`\`\`

### خطای "No module named 'paramiko'"

\`\`\`bash
pip3 install paramiko
\`\`\`

## اگر همچنان مشکل دارید

1. تمام فایل‌های این پروژه را دوباره از GitHub یا منبع اصلی دانلود کنید
2. مطمئن شوید که در پوشه صحیح (telegram-bot/) هستید
3. مطمئن شوید Python 3.7 یا بالاتر نصب است
4. لاگ کامل خطا را بررسی کنید
