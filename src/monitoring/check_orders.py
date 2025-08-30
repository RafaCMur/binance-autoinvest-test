import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from decimal import getcontext, Decimal
from binance.spot import Spot
from datetime import datetime, timezone
from src.utils.logger import log_trade
from src.utils.telegram import send_telegram
from config.settings import (
    USE_TESTNET, BASE_URL, API_KEY, API_SECRET,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    TRADING_PAIR, BASE_CURRENCY, TARGET_CURRENCY
)

getcontext().prec = 28

# Print clear environment indicator
print(f"ENVIRONMENT: {'TESTNET (Safe Mode)' if USE_TESTNET else 'MAINNET (Real Money)'}")
print(f"API URL: {BASE_URL if USE_TESTNET else 'https://api.binance.com'}")
print(f"Trading Pair: {TRADING_PAIR}")
print(f"Strategy: Check Orders")
print("-" * 50)

client = Spot(api_key=API_KEY, api_secret=API_SECRET, base_url=BASE_URL)

# Config
SYMBOL = TRADING_PAIR

def check_and_notify_executions():
    """Check for recently executed orders and send Telegram notifications"""
    
    print(f"\n========== CHECKING ORDER EXECUTIONS ==========")
    print("Datetime (UTC):", datetime.now(timezone.utc).isoformat())
    print("===============================================")
    
    try:
        # Get recent trades (last 24 hours)
        trades = client.my_trades(symbol=SYMBOL, limit=10)
        
        if not trades:
            print("No recent trades found")
            return
        
        # Check for trades from the last hour (3600000 ms)
        current_time = int(datetime.now(timezone.utc).timestamp() * 1000)
        recent_threshold = current_time - (60 * 60 * 1000)  # 1 hour ago
        
        recent_executions = [t for t in trades if t['time'] > recent_threshold]
        
        if not recent_executions:
            print("No executions in the last hour")
            return
        
        for trade in recent_executions:
            qty = Decimal(trade['qty'])
            price = Decimal(trade['price'])
            fee = Decimal(trade['commission'])
            total_cost = qty * price
            trade_time = datetime.fromtimestamp(trade['time'] / 1000, timezone.utc)
            
            print(f"Recent execution: {qty} BTC @ {price} {BASE_CURRENCY}")
            
            # Send Telegram notification
            from src.utils.telegram import send_telegram
            
            message = (
                f"DIP ORDER EXECUTED! {'(TESTNET)' if USE_TESTNET else '(MAINNET)'}\n\n"
                f"Trading Pair: {SYMBOL}\n"
                f"Order Type: Limit Order Fill\n"
                f"Quantity: {qty} BTC\n"
                f"Execution Price: {price} {BASE_CURRENCY}\n"
                f"Total Cost: {total_cost:.2f} {BASE_CURRENCY}\n"
                f"Trading Fee: {fee} BTC\n"
                f"Order ID: {trade['orderId']}\n"
                f"Trade ID: {trade['id']}\n"
                f"Execution Time: {trade_time.strftime('%d/%m/%Y %H:%M:%S')} UTC\n\n"
                f"Your buy-the-dip limit order was filled successfully!\n"
                f"Market dipped to your target price and triggered the purchase."
            )
            
            try:
                sent = send_telegram(message, parse_mode=None)
                print(f"Telegram notification sent: {sent}")
            except Exception as e:
                print(f"Telegram error: {e}")
    
    except Exception as e:
        print(f"Error checking executions: {e}")
        # Send error notification
        try:
            error_msg = f"Error checking order executions: {str(e)}"
            send_telegram(error_msg, parse_mode=None)
        except:
            pass

if __name__ == "__main__":
    check_and_notify_executions()
