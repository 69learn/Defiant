# راهنمای تنظیم دیتابیس MySQL

## مشکل فعلی
\`\`\`
خطا در اتصال به دیتابیس: 1698 (28000): Access denied for user 'root'@'localhost'
\`\`\`

این خطا به این دلیل رخ میده که MySQL به کاربر root بدون پسورد اجازه اتصال نمیده.

## راه حل 1: تنظیم پسورد برای کاربر root

\`\`\`bash
# وارد MySQL شوید
sudo mysql -u root

# پسورد جدید تنظیم کنید
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_strong_password';
FLUSH PRIVILEGES;
EXIT;
\`\`\`

سپس در فایل `.env` پسورد را تنظیم کنید:
\`\`\`
MYSQL_PASSWORD=your_strong_password
\`\`\`

## راه حل 2: ایجاد کاربر جدید (توصیه میشه)

\`\`\`bash
# وارد MySQL شوید
sudo mysql -u root

# کاربر جدید بسازید
CREATE USER 'telegram_bot'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON telegram_bot.* TO 'telegram_bot'@'localhost';
FLUSH PRIVILEGES;
EXIT;
\`\`\`

سپس در فایل `.env` اطلاعات را تغییر دهید:
\`\`\`
MYSQL_USER=telegram_bot
MYSQL_PASSWORD=strong_password_here
MYSQL_DATABASE=telegram_bot
\`\`\`

## راه حل 3: استفاده از اسکریپت خودکار

\`\`\`bash
# اجرای اسکریپت setup
chmod +x setup_database.sh
sudo ./setup_database.sh
\`\`\`

این اسکریپت به صورت خودکار:
- دیتابیس telegram_bot را میسازد
- کاربر telegram_bot را ایجاد میکند
- دسترسی‌های لازم را میدهد
- جداول را ایجاد میکند

## تست اتصال

بعد از تنظیم، برای تست اتصال:

\`\`\`bash
# تست با دستور mysql
mysql -u telegram_bot -p telegram_bot

# یا اجرای اسکریپت تست
python3 test_db.py
\`\`\`

## نکات مهم

1. همیشه از پسورد قوی استفاده کنید
2. فایل `.env` را در `.gitignore` قرار دهید
3. برای production از کاربر جداگانه استفاده کنید (نه root)
4. بک‌آپ منظم از دیتابیس بگیرید
