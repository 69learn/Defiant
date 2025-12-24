import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

ADMIN_IDS = [8045668836, 1491809706]

# MySQL
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'telegram_bot')
MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))

# Flask
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')

# Payment
CARD_NUMBER = os.getenv('CARD_NUMBER', '6037997740087599')
CARD_HOLDER = os.getenv('CARD_HOLDER', 'مهدی رستگاری')
CARD_BANK = os.getenv('CARD_BANK', 'بانک ملی')
MIN_PAYMENT_AMOUNT = int(os.getenv('MIN_PAYMENT_AMOUNT', '100000'))

# Crypto Payment
TRON_WALLET_ADDRESS = os.getenv('TRON_WALLET_ADDRESS', 'TM9PdcVptFWBdb49DRgqru1wYXbVGnnSDh')
TRONGRID_API_KEY = os.getenv('TRONGRID_API_KEY', '')  # Optional, for higher rate limits
CRYPTO_PAYMENT_TIMEOUT_MINUTES = int(os.getenv('CRYPTO_PAYMENT_TIMEOUT_MINUTES', '20'))
USDT_TO_TOMAN_RATE = float(os.getenv('USDT_TO_TOMAN_RATE', '72000'))  # Default rate, will be updated from API
