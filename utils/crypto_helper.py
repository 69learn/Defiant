import requests
import time
from datetime import datetime, timedelta
import pytz
from config import TRONGRID_API_KEY, USDT_TO_TOMAN_RATE

def get_usdt_to_toman_rate():
    """
    Get current USDT to Toman exchange rate
    Returns the rate or default if API fails
    """
    try:
        # Using Nobitex API for Iranian Toman rate
        response = requests.get('https://api.nobitex.ir/v2/orderbook/USDTIRT', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if 'asks' in data and len(data['asks']) > 0:
                rate = float(data['asks'][0][0]) / 10  # Convert Rial to Toman
                return rate
    except Exception as e:
        print(f"Error fetching USDT rate: {e}")
    
    return USDT_TO_TOMAN_RATE

def toman_to_tron(toman_amount):
    """
    Convert Toman amount to TRON (USDT TRC20)
    """
    rate = get_usdt_to_toman_rate()
    usdt_amount = toman_amount / rate
    return round(usdt_amount, 6)

def check_tron_payment(wallet_address, expected_amount, start_timestamp, timeout_minutes=20):
    """
    Check if payment was received on Tron network
    
    Args:
        wallet_address: The wallet address to check
        expected_amount: Expected USDT amount (in USDT)
        start_timestamp: Unix timestamp when payment was initiated
        timeout_minutes: Payment timeout in minutes
    
    Returns:
        dict: {'success': bool, 'amount': float, 'txid': str} or None
    """
    try:
        # TronGrid API endpoint
        base_url = "https://api.trongrid.io"
        
        headers = {}
        if TRONGRID_API_KEY:
            headers['TRON-PRO-API-KEY'] = TRONGRID_API_KEY
        
        # Get TRC20 transactions for the wallet
        url = f"{base_url}/v1/accounts/{wallet_address}/transactions/trc20"
        params = {
            'limit': 50,
            'order_by': 'block_timestamp,desc'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"TronGrid API error: {response.status_code}")
            return None
        
        data = response.json()
        
        if 'data' not in data or not data['data']:
            return None
        
        # USDT TRC20 contract address
        USDT_CONTRACT = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'
        
        timeout_timestamp = start_timestamp + (timeout_minutes * 60 * 1000)  # Convert to milliseconds
        
        for tx in data['data']:
            # Check if it's USDT and sent to our wallet
            if (tx.get('token_info', {}).get('address') == USDT_CONTRACT and
                tx.get('to') == wallet_address and
                tx.get('type') == 'Transfer'):
                
                tx_timestamp = tx.get('block_timestamp', 0)
                
                # Check if transaction is within the payment window
                if start_timestamp <= tx_timestamp <= timeout_timestamp:
                    # USDT has 6 decimals
                    amount = float(tx.get('value', 0)) / 1000000
                    
                    # Allow 1% tolerance for amount verification
                    if amount >= expected_amount * 0.99:
                        return {
                            'success': True,
                            'amount': amount,
                            'txid': tx.get('transaction_id', '')
                        }
        
        return None
        
    except Exception as e:
        print(f"Error checking Tron payment: {e}")
        return None

def get_jalali_datetime():
    """
    Get current datetime in Persian/Jalali format with Tehran timezone
    """
    try:
        from persiantools.jdatetime import JalaliDateTime
        tehran_tz = pytz.timezone('Asia/Tehran')
        now = datetime.now(tehran_tz)
        jalali_now = JalaliDateTime(now)
        return jalali_now.strftime('%Y/%m/%d - %H:%M:%S')
    except ImportError:
        # Fallback to Gregorian with Tehran timezone if persiantools not available
        tehran_tz = pytz.timezone('Asia/Tehran')
        now = datetime.now(tehran_tz)
        return now.strftime('%Y/%m/%d - %H:%M:%S')
