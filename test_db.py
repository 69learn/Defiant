#!/usr/bin/env python3
"""
اسکریپت تست اتصال به دیتابیس
"""

import sys
from database import get_connection, init_database
from config import MYSQL_HOST, MYSQL_USER, MYSQL_DATABASE, MYSQL_PORT

def test_connection():
    """تست اتصال به دیتابیس"""
    print("🔍 در حال تست اتصال به دیتابیس...")
    print(f"   Host: {MYSQL_HOST}")
    print(f"   User: {MYSQL_USER}")
    print(f"   Database: {MYSQL_DATABASE}")
    print(f"   Port: {MYSQL_PORT}")
    print()
    
    connection = get_connection()
    
    if connection is None:
        print("❌ اتصال به دیتابیس ناموفق بود!")
        print()
        print("راهنمای حل مشکل:")
        print("1. فایل .env را بررسی کنید")
        print("2. مطمئن شوید MySQL در حال اجرا است: sudo systemctl status mysql")
        print("3. اطلاعات کاربری را بررسی کنید")
        print("4. راهنمای DATABASE_SETUP.md را مطالعه کنید")
        return False
    
    print("✓ اتصال به دیتابیس موفق بود!")
    
    # تست کوئری
    cursor = connection.cursor()
    try:
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        print()
        print(f"📊 جداول موجود ({len(tables)} عدد):")
        for table in tables:
            print(f"   - {table[0]}")
        
        if len(tables) == 0:
            print()
            print("⚠️  هیچ جدولی وجود ندارد. در حال ایجاد جداول...")
            if init_database():
                print("✓ جداول با موفقیت ایجاد شدند")
            else:
                print("❌ خطا در ایجاد جداول")
                return False
        
        # شمارش رکوردها
        print()
        print("📈 تعداد رکوردها:")
        for table in ['users', 'tunnels', 'tunnel_configs', 'panels']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   - {table}: {count}")
            except:
                pass
        
        print()
        print("🎉 دیتابیس آماده استفاده است!")
        return True
        
    except Exception as e:
        print(f"❌ خطا در اجرای کوئری: {e}")
        return False
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
