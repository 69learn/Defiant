#!/usr/bin/env python3
"""
Interactive MySQL Setup Script
This script helps you set up MySQL database for the Telegram Bot
"""

import os
import subprocess
import sys

def run_command(command, input_text=None):
    """Run a shell command and return output"""
    try:
        if input_text:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                input=input_text
            )
        else:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True
            )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def print_header(text):
    """Print a formatted header"""
    print("\n" + "="*60)
    print(text.center(60))
    print("="*60 + "\n")

def main():
    print_header("MySQL Setup for Telegram Bot")
    
    print("این اسکریپت به شما کمک می‌کند MySQL را برای ربات راه‌اندازی کنید.\n")
    
    # Check if MySQL is installed
    print("🔍 در حال بررسی نصب MySQL...")
    success, _, _ = run_command("which mysql")
    
    if not success:
        print("❌ MySQL نصب نیست!")
        print("\nلطفاً ابتدا MySQL را نصب کنید:")
        print("  sudo apt update")
        print("  sudo apt install mysql-server -y")
        sys.exit(1)
    
    print("✅ MySQL نصب شده است\n")
    
    # Method selection
    print("لطفاً یک روش را انتخاب کنید:")
    print("1. استفاده از MySQL root با پسورد جدید")
    print("2. ایجاد کاربر جدید برای ربات")
    print("3. نمایش دستورات manual برای اجرای دستی")
    
    choice = input("\nانتخاب شما (1-3): ").strip()
    
    if choice == "1":
        setup_root_password()
    elif choice == "2":
        create_new_user()
    elif choice == "3":
        show_manual_commands()
    else:
        print("❌ انتخاب نامعتبر!")
        sys.exit(1)

def setup_root_password():
    """Setup MySQL root password"""
    print_header("تنظیم پسورد root")
    
    print("⚠️  توجه: این روش پسورد root را تغییر می‌دهد\n")
    
    new_password = input("پسورد جدید برای root: ").strip()
    if not new_password:
        print("❌ پسورد نمی‌تواند خالی باشد!")
        sys.exit(1)
    
    print("\n🔧 در حال تنظیم پسورد...")
    
    # Commands to set root password
    sql_commands = f"""
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{new_password}';
FLUSH PRIVILEGES;
CREATE DATABASE IF NOT EXISTS telegram_bot;
USE telegram_bot;
"""
    
    success, stdout, stderr = run_command(
        "sudo mysql",
        input_text=sql_commands
    )
    
    if success:
        print("✅ پسورد root با موفقیت تنظیم شد!")
        update_env_file('root', new_password)
    else:
        print(f"❌ خطا در تنظیم پسورد: {stderr}")
        print("\nلطفاً دستورات زیر را به صورت دستی اجرا کنید:")
        print("  sudo mysql")
        print(f"  ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '{new_password}';")
        print("  FLUSH PRIVILEGES;")
        print("  CREATE DATABASE IF NOT EXISTS telegram_bot;")
        print("  exit")

def create_new_user():
    """Create a new MySQL user for the bot"""
    print_header("ایجاد کاربر جدید")
    
    db_user = input("نام کاربری (پیشنهاد: tunbot): ").strip() or "tunbot"
    db_password = input("پسورد: ").strip()
    
    if not db_password:
        print("❌ پسورد نمی‌تواند خالی باشد!")
        sys.exit(1)
    
    print(f"\n🔧 در حال ایجاد کاربر {db_user}...")
    
    sql_commands = f"""
CREATE DATABASE IF NOT EXISTS telegram_bot;
CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '{db_password}';
GRANT ALL PRIVILEGES ON telegram_bot.* TO '{db_user}'@'localhost';
FLUSH PRIVILEGES;
"""
    
    success, stdout, stderr = run_command(
        "sudo mysql",
        input_text=sql_commands
    )
    
    if success:
        print(f"✅ کاربر {db_user} با موفقیت ایجاد شد!")
        update_env_file(db_user, db_password)
    else:
        print(f"❌ خطا در ایجاد کاربر: {stderr}")
        print("\nلطفاً دستورات زیر را به صورت دستی اجرا کنید:")
        print("  sudo mysql")
        print("  CREATE DATABASE IF NOT EXISTS telegram_bot;")
        print(f"  CREATE USER IF NOT EXISTS '{db_user}'@'localhost' IDENTIFIED BY '{db_password}';")
        print(f"  GRANT ALL PRIVILEGES ON telegram_bot.* TO '{db_user}'@'localhost';")
        print("  FLUSH PRIVILEGES;")
        print("  exit")

def show_manual_commands():
    """Show manual commands"""
    print_header("دستورات Manual")
    
    print("برای راه‌اندازی دستی MySQL، این دستورات را اجرا کنید:\n")
    print("1. وارد MySQL شوید:")
    print("   sudo mysql\n")
    
    print("2. دیتابیس و کاربر بسازید:")
    print("   CREATE DATABASE IF NOT EXISTS telegram_bot;")
    print("   CREATE USER IF NOT EXISTS 'tunbot'@'localhost' IDENTIFIED BY 'YOUR_PASSWORD';")
    print("   GRANT ALL PRIVILEGES ON telegram_bot.* TO 'tunbot'@'localhost';")
    print("   FLUSH PRIVILEGES;")
    print("   exit\n")
    
    print("3. فایل .env را ویرایش کنید:")
    print("   nano .env\n")
    
    print("4. این خطوط را اضافه کنید:")
    print("   MYSQL_USER=tunbot")
    print("   MYSQL_PASSWORD=YOUR_PASSWORD")
    print("   MYSQL_DATABASE=telegram_bot")

def update_env_file(username, password):
    """Update .env file with database credentials"""
    print("\n📝 در حال به‌روزرسانی فایل .env...")
    
    env_path = ".env"
    env_content = []
    
    # Read existing .env if exists
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            env_content = f.readlines()
    
    # Update or add database credentials
    updated = {
        'MYSQL_USER': False,
        'MYSQL_PASSWORD': False,
        'MYSQL_DATABASE': False
    }
    
    for i, line in enumerate(env_content):
        if line.startswith('MYSQL_USER='):
            env_content[i] = f'MYSQL_USER={username}\n'
            updated['MYSQL_USER'] = True
        elif line.startswith('MYSQL_PASSWORD='):
            env_content[i] = f'MYSQL_PASSWORD={password}\n'
            updated['MYSQL_PASSWORD'] = True
        elif line.startswith('MYSQL_DATABASE='):
            env_content[i] = f'MYSQL_DATABASE=telegram_bot\n'
            updated['MYSQL_DATABASE'] = True
    
    # Add missing entries
    if not updated['MYSQL_USER']:
        env_content.append(f'MYSQL_USER={username}\n')
    if not updated['MYSQL_PASSWORD']:
        env_content.append(f'MYSQL_PASSWORD={password}\n')
    if not updated['MYSQL_DATABASE']:
        env_content.append(f'MYSQL_DATABASE=telegram_bot\n')
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.writelines(env_content)
    
    print("✅ فایل .env به‌روزرسانی شد!")
    
    print("\n" + "="*60)
    print("✅ راه‌اندازی با موفقیت انجام شد!")
    print("="*60)
    print("\nحالا می‌توانید ربات را اجرا کنید:")
    print("  python3 test_db.py        # تست اتصال دیتابیس")
    print("  python3 telegram_bot.py   # اجرای ربات")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ لغو شد توسط کاربر")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ خطای غیرمنتظره: {e}")
        sys.exit(1)
