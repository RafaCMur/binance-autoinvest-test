from binance.spot import Spot
from dotenv import load_dotenv
import os

load_dotenv()

USE_TESTNET = os.getenv("USE_TESTNET", "true").lower() == "true"
BASE_URL = "https://testnet.binance.vision" if USE_TESTNET else None

API_KEY = os.getenv("BINANCE_API_KEY_TEST")
API_SECRET = os.getenv("BINANCE_API_SECRET_TEST")

client = Spot(api_key=API_KEY, api_secret=API_SECRET, base_url=BASE_URL)

# ===== Config =====
SYMBOL = "BTCUSDT"   # change to BTCEUR in mainnet if using EUR

# ===== Script =====
print("========== OPEN ORDERS ==========")
open_orders = client.get_open_orders(symbol=SYMBOL)

if not open_orders:
    print(f"No open orders found for {SYMBOL}")
else:
    for order in open_orders:
        print("----------------------------------")
        print(f"Order ID   : {order['orderId']}")
        print(f"Symbol     : {order['symbol']}")
        print(f"Side       : {order['side']}")
        print(f"Type       : {order['type']}")
        print(f"Status     : {order['status']}")
        print(f"Price      : {order['price']}")
        print(f"Quantity   : {order['origQty']}")
        print(f"Executed   : {order['executedQty']}")
        print(f"TimeInForce: {order['timeInForce']}")
        print(f"Client ID  : {order['clientOrderId']}")
print("=================================")
