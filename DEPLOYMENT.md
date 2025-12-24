# راهنمای نصب و راه‌اندازی ربات

## پیش‌نیازها

### 1. سرور
- سرور لینوکس (Ubuntu/Debian توصیه میشه)
- دسترسی root یا sudo
- Python 3.8 یا بالاتر
- MySQL/MariaDB

### 2. دیتابیس MySQL
نصب MySQL:
\`\`\`bash
apt update
apt install mysql-server -y
\`\`\`

ایجاد دیتابیس و کاربر:
\`\`\`bash
mysql -u root -p
\`\`\`

\`\`\`sql
CREATE DATABASE telegram_bot;
CREATE USER 'botuser'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON telegram_bot.* TO 'botuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;
\`\`\`

### 3. نصب وابستگی‌های Python
\`\`\`bash
apt install python3-pip python3-venv -y
\`\`\`

## نصب ربات

### مرحله 1: دانلود کد
\`\`\`bash
cd /root
git clone https://your-repo-url/telegram-bot.git
cd telegram-bot
\`\`\`

یا اگر فایل ZIP دارید:
\`\`\`bash
cd /root
unzip telegram-bot.zip
cd telegram-bot
\`\`\`

### مرحله 2: ایجاد محیط مجازی Python
\`\`\`bash
python3 -m venv venv
source venv/bin/activate
\`\`\`

### مرحله 3: نصب کتابخانه‌ها
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### مرحله 4: تنظیم environment variables
کپی کردن فایل نمونه:
\`\`\`bash
cp .env.example .env
nano .env
\`\`\`

محتوای فایل .env:
\`\`\`bash
# Bot Configuration
BOT_TOKEN=your_bot_token_here

# MySQL Configuration
MYSQL_HOST=localhost
MYSQL_USER=botuser
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=telegram_bot
MYSQL_PORT=3306

# Admin User ID (Optional)
ADMIN_USER_ID=your_telegram_user_id
\`\`\`

**دریافت Bot Token:**
1. به @BotFather در تلگرام پیام بدید
2. دستور `/newbot` رو بفرستید
3. نام و username ربات رو وارد کنید
4. توکن دریافتی رو در فایل .env قرار بدید

### مرحله 5: اجرای ربات
\`\`\`bash
chmod +x runbot.sh
./runbot.sh
\`\`\`

یا به صورت دستی:
\`\`\`bash
source venv/bin/activate
python3 telegram_bot.py
\`\`\`

## اجرای ربات به صورت سرویس

برای اینکه ربات همیشه در پس‌زمینه اجرا بشه:

### ایجاد سرویس systemd
\`\`\`bash
nano /etc/systemd/system/telegram-bot.service
\`\`\`

محتوا:
\`\`\`ini
[Unit]
Description=Telegram Bot for Tunnel Management
After=network.target mysql.service

[Service]
Type=simple
User=root
WorkingDirectory=/root/telegram-bot
Environment="PATH=/root/telegram-bot/venv/bin"
ExecStart=/root/telegram-bot/venv/bin/python3 /root/telegram-bot/telegram_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
\`\`\`

فعال‌سازی و اجرای سرویس:
\`\`\`bash
systemctl daemon-reload
systemctl enable telegram-bot.service
systemctl start telegram-bot.service
\`\`\`

بررسی وضعیت:
\`\`\`bash
systemctl status telegram-bot.service
\`\`\`

مشاهده لاگ‌ها:
\`\`\`bash
journalctl -u telegram-bot.service -f
\`\`\`

## بروزرسانی ربات

\`\`\`bash
cd /root/telegram-bot
systemctl stop telegram-bot.service
git pull  # یا کپی فایل‌های جدید
source venv/bin/activate
pip install -r requirements.txt --upgrade
systemctl start telegram-bot.service
\`\`\`

## حل مشکلات رایج

### ربات شروع نمیشه
1. چک کنید که توکن درست باشه:
\`\`\`bash
cat .env | grep BOT_TOKEN
\`\`\`

2. چک کنید دیتابیس در دسترس باشه:
\`\`\`bash
mysql -u botuser -p telegram_bot
\`\`\`

3. مشاهده لاگ‌های خطا:
\`\`\`bash
journalctl -u telegram-bot.service -n 50
\`\`\`

### خطای اتصال به دیتابیس
\`\`\`bash
# بررسی وضعیت MySQL
systemctl status mysql

# تست اتصال
mysql -u botuser -p telegram_bot
\`\`\`

### خطای import
\`\`\`bash
# نصب مجدد وابستگی‌ها
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
\`\`\`

### خطای دسترسی SSH
مطمئن بشید که:
- پورت SSH روی سرورهای هدف باز باشه
- فایروال اجازه اتصال بده
- اطلاعات SSH (username/password) صحیح باشه

## امنیت

1. فایل .env رو از git ignore کنید
2. رمزهای قوی برای دیتابیس استفاده کنید
3. فقط به کاربران مورد اعتماد دسترسی بدید
4. فایروال رو فعال نگه دارید
5. لاگ‌ها رو به صورت منظم چک کنید

## پشتیبان‌گیری

### دیتابیس
\`\`\`bash
mysqldump -u botuser -p telegram_bot > backup_$(date +%Y%m%d).sql
\`\`\`

### بازگردانی از بکآپ
\`\`\`bash
mysql -u botuser -p telegram_bot < backup_20250128.sql
