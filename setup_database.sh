#!/bin/bash

# رنگ‌ها برای خروجی
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🔧 راه‌اندازی دیتابیس MySQL برای Telegram Bot${NC}"
echo ""

# خواندن اطلاعات از کاربر
read -p "نام دیتابیس (پیش‌فرض: telegram_bot): " DB_NAME
DB_NAME=${DB_NAME:-telegram_bot}

read -p "نام کاربر دیتابیس (پیش‌فرض: telegram_bot): " DB_USER
DB_USER=${DB_USER:-telegram_bot}

read -sp "پسورد دیتابیس: " DB_PASS
echo ""

if [ -z "$DB_PASS" ]; then
    echo -e "${RED}❌ پسورد نمیتواند خالی باشد!${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}📝 در حال ایجاد دیتابیس و کاربر...${NC}"

# اجرای دستورات MySQL
sudo mysql -u root << EOF
-- ایجاد دیتابیس
CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- ایجاد کاربر (حذف اگر قبلاً وجود داشته)
DROP USER IF EXISTS '$DB_USER'@'localhost';
CREATE USER '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASS';

-- دادن دسترسی‌ها
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USER'@'localhost';
FLUSH PRIVILEGES;

-- نمایش دیتابیس‌ها
SHOW DATABASES;
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ دیتابیس و کاربر با موفقیت ایجاد شدند${NC}"
    
    # به‌روزرسانی فایل .env
    if [ -f .env ]; then
        echo -e "${YELLOW}📝 در حال به‌روزرسانی فایل .env...${NC}"
        
        # بک‌آپ از .env
        cp .env .env.backup
        
        # به‌روزرسانی مقادیر
        sed -i "s/^MYSQL_USER=.*/MYSQL_USER=$DB_USER/" .env
        sed -i "s/^MYSQL_PASSWORD=.*/MYSQL_PASSWORD=$DB_PASS/" .env
        sed -i "s/^MYSQL_DATABASE=.*/MYSQL_DATABASE=$DB_NAME/" .env
        
        echo -e "${GREEN}✓ فایل .env به‌روزرسانی شد (بک‌آپ در .env.backup)${NC}"
    else
        echo -e "${YELLOW}⚠️  فایل .env پیدا نشد. از .env.example کپی کنید:${NC}"
        echo "cp .env.example .env"
    fi
    
    echo ""
    echo -e "${YELLOW}📊 در حال ایجاد جداول...${NC}"
    
    # اجرای اسکریپت ایجاد جداول
    python3 << PYEOF
from database import init_database
if init_database():
    print("${GREEN}✓ جداول با موفقیت ایجاد شدند${NC}")
else:
    print("${RED}❌ خطا در ایجاد جداول${NC}")
PYEOF
    
    echo ""
    echo -e "${GREEN}🎉 راه‌اندازی دیتابیس کامل شد!${NC}"
    echo ""
    echo -e "${YELLOW}اطلاعات دیتابیس:${NC}"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    echo "  Password: ********"
    echo ""
    echo -e "${YELLOW}برای تست اتصال:${NC}"
    echo "  python3 test_db.py"
    echo ""
    echo -e "${YELLOW}برای اجرای ربات:${NC}"
    echo "  ./runbot.sh"
    
else
    echo -e "${RED}❌ خطا در ایجاد دیتابیس${NC}"
    echo "لطفاً بررسی کنید که MySQL نصب شده و در حال اجرا است:"
    echo "  sudo systemctl status mysql"
    exit 1
fi
