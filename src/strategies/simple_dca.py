from binance.spot import Spot
from dotenv import load_dotenv
import os
from decimal import Decimal, ROUND_DOWN, getcontext
from datetime import datetime, timezone
from src.utils.logger import log_trade

load_dotenv()
getcontext().prec = 28

USE_TESTNET = os.getenv("USE_TESTNET", "false").lower() == "true"
BASE_URL = "https://testnet.binance.vision" if USE_TESTNET else None

# Use mainnet keys by default
if USE_TESTNET:
    API_KEY = os.getenv("BINANCE_API_KEY_TEST")
    API_SECRET = os.getenv("BINANCE_API_SECRET_TEST")
else:
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Spot(api_key=API_KEY, api_secret=API_SECRET, base_url=BASE_URL)

def get_balance(asset: str) -> Decimal:
    acc = client.account()
    bal = next((b for b in acc["balances"] if b["asset"] == asset), None)
    return Decimal(bal["free"]) if bal else Decimal("0")

# Config
SYMBOL = "BTCEUR" if not USE_TESTNET else "BTCUSDT"
BASE_CURRENCY = "EUR" if not USE_TESTNET else "USDT"
AMOUNT = Decimal("10.00")

print("========== SIMPLE DCA TEST ==========")
print("Datetime (UTC):", datetime.now(timezone.utc).isoformat())
print(f"Environment: {'TESTNET' if USE_TESTNET else 'MAINNET'}")
print("====================================")

base_before = get_balance(BASE_CURRENCY)
btc_before = get_balance("BTC")
print(f"{BASE_CURRENCY} available: {base_before}")
print(f"BTC available: {btc_before}")

# Safety check for real money
if not USE_TESTNET:
    if base_before < AMOUNT * 2:
        raise Exception(f"Insufficient {BASE_CURRENCY} balance. Need at least {AMOUNT * 2} for safety")

print(f"\nExecuting market buy: {AMOUNT} {BASE_CURRENCY} -> BTC")

# Execute order
order = client.new_order(
    symbol=SYMBOL,
    side="BUY",
    type="MARKET",
    quoteOrderQty=str(AMOUNT)
)

# Process order fills
btc_bought = Decimal("0")
cost_total = Decimal("0")
commission = Decimal("0")
avg_price = Decimal("0")

for fill in order.get("fills", []):
    qty = Decimal(fill['qty'])
    price = Decimal(fill['price'])
    fee = Decimal(fill['commission'])
    btc_bought += qty
    cost_total += qty * price
    commission += fee
    print(f"Fill: {qty} BTC @ {price} {BASE_CURRENCY} (fee: {fee} {fill['commissionAsset']})")

if btc_bought > 0:
    avg_price = cost_total / btc_bought

print("========== ORDER EXECUTED ==========")
print(f"Order ID: {order['orderId']}")
print(f"Symbol: {order['symbol']}")
print(f"Status: {order['status']}")
print(f"BTC Purchased: {btc_bought}")
print(f"Total Cost: {cost_total:.2f} {BASE_CURRENCY}")
print(f"Average Price: {avg_price:.2f} {BASE_CURRENCY}")
print(f"Commission: {commission} BTC")
print("===================================")

# Final balances
base_after = get_balance(BASE_CURRENCY)
btc_after = get_balance("BTC")

print("========== FINAL BALANCES ==========")
print(f"{BASE_CURRENCY}: {base_before} -> {base_after} ({base_after - base_before:+.2f})")
print(f"BTC: {btc_before} -> {btc_after} ({btc_after - btc_before:+.8f})")
print("===================================")

# Log to CSV
log_trade(
    action="simple_dca",
    symbol=SYMBOL,
    base_amount=AMOUNT,
    btc_qty=btc_bought,
    price=avg_price,
    fee=commission,
    dip_price=None,
    dip_qty=None,
    base_before=base_before,
    base_after=base_after,
    btc_before=btc_before,
    btc_after=btc_after,
    base_currency=BASE_CURRENCY
)
print("Trade logged to history.csv")

# Telegram notification
from telegram_notify import send_telegram

summary = (
    f"Simple DCA Purchase Executed {'(TESTNET)' if USE_TESTNET else '(MAINNET)'}\n\n"
    f"Trading Pair: {SYMBOL}\n"
    f"Purchase Amount: {AMOUNT} {BASE_CURRENCY}\n"
    f"Bitcoin Purchased: {btc_bought}\n"
    f"Average Price: {avg_price:.2f} {BASE_CURRENCY}\n"
    f"Trading Fee: {commission} BTC\n\n"
    f"{BASE_CURRENCY} Balance: {base_before} -> {base_after} ({base_after - base_before:+.2f})\n"
    f"BTC Balance: {btc_before} -> {btc_after} ({btc_after - btc_before:+.8f})\n\n"
    f"Strategy: Simple DCA market buy only\n"
    f"Executed: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')} UTC"
)

try:
    sent = send_telegram(summary, parse_mode=None)
    print(f"Telegram notification sent: {sent}")
except Exception as e:
    print(f"Telegram error (ignored): {e}")
