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
SYMBOL = "BTCUSDT"   # change to BTCEUR for mainnet with EUR balance

# ===== Script =====
print("========== CANCEL ALL ORDERS ==========")
open_orders = client.get_open_orders(symbol=SYMBOL)

if not open_orders:
    print(f"No open orders found for {SYMBOL}")
else:
    for order in open_orders:
        oid = order["orderId"]
        price = order.get("price", "?")
        side = order.get("side", "?")
        print(f"Cancelling order {oid} | Side: {side} | Price: {price}")
        client.cancel_order(symbol=SYMBOL, orderId=oid)

print("Done.")
print("=======================================")
