#!/bin/bash

# رنگ‌ها برای چاپ
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[*] شروع نصب ربات تلگرام...${NC}"

# بررسی Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[!] Python3 نصب نیست${NC}"
    exit 1
fi

echo -e "${GREEN}[+] Python3 نصب شده است${NC}"

# بررسی MySQL
if ! command -v mysql &> /dev/null; then
    echo -e "${YELLOW}[*] MySQL نصب نیست، در حال نصب...${NC}"
    apt-get update
    apt-get install -y mysql-server
fi

echo -e "${GREEN}[+] MySQL نصب شده است${NC}"

# ایجاد Virtual Environment
echo -e "${YELLOW}[*] ایجاد Virtual Environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# نصب وابستگی‌ها
echo -e "${YELLOW}[*] نصب وابستگی‌های Python...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}[+] نصب کامل شد${NC}"
echo -e "${YELLOW}[*] لطفاً فایل .env را تنظیم کنید و دستور زیر را اجرا کنید:${NC}"
echo -e "${GREEN}python3 telegram_bot.py${NC}"
