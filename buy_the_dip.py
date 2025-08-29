from binance.spot import Spot
from dotenv import load_dotenv
from decimal import Decimal, ROUND_DOWN, getcontext
import os
from datetime import datetime, timezone
from logger_csv import log_trade

load_dotenv()
getcontext().prec = 28

USE_TESTNET = os.getenv("USE_TESTNET", "true").lower() == "true"
BASE_URL = "https://testnet.binance.vision" if USE_TESTNET else None

API_KEY = os.getenv("BINANCE_API_KEY_TEST")
API_SECRET = os.getenv("BINANCE_API_SECRET_TEST")

client = Spot(api_key=API_KEY, api_secret=API_SECRET, base_url=BASE_URL)

# ===== Config =====
SYMBOL = "BTCUSDT"          # in mainnet you can switch to BTCEUR
BASELINE_AMOUNT = Decimal("10.00")  # baseline buy amount
DIP_PERCENT = Decimal("0.02")       # -2% dip level

# ===== Utils =====
def get_balance(asset: str) -> Decimal:
    """Return free balance of a given asset"""
    acc = client.account()
    bal = next((b for b in acc["balances"] if b["asset"] == asset), None)
    return Decimal(bal["free"]) if bal else Decimal("0")

def cancel_old_orders():
    """Cancel all open orders for the symbol"""
    open_orders = client.get_open_orders(symbol=SYMBOL)
    for o in open_orders:
        print(f"Cancelling old order: {o['orderId']} @ {o['price']}")
        client.cancel_order(symbol=SYMBOL, orderId=o["orderId"])

def get_filters(symbol):
    """Retrieve lot size, price tick size and min notional filters"""
    info = client.exchange_info(symbol=symbol)["symbols"][0]["filters"]
    f = {f["filterType"]: f for f in info}
    return {
        "stepSize": Decimal(f["LOT_SIZE"]["stepSize"]),
        "minQty": Decimal(f["LOT_SIZE"]["minQty"]),
        "tickSize": Decimal(f["PRICE_FILTER"]["tickSize"]),
        "minNotional": Decimal(f.get("MIN_NOTIONAL", {}).get("minNotional", "0"))
    }

def floor_step(value: Decimal, step: Decimal) -> Decimal:
    """Round down value to the nearest valid step"""
    return (value // step) * step

# ===== Script =====
print("\n========== START EXECUTION ==========")
print("Datetime (UTC):", datetime.now(timezone.utc).isoformat())
print("=====================================")

usdt_before = get_balance("USDT")
btc_before = get_balance("BTC")
print(f"Initial USDT balance : {usdt_before}")
print(f"Initial BTC balance  : {btc_before}")
print("-------------------------------------")

# Cancel old limit orders
cancel_old_orders()

# Current price
price_now = Decimal(client.ticker_price(SYMBOL)["price"])
print(f"Current {SYMBOL} price: {price_now} USDT\n")

# 1) Baseline market buy
print(f"Executing BASELINE market buy of {BASELINE_AMOUNT} USDT...")
base_order = client.new_order(
    symbol=SYMBOL,
    side="BUY",
    type="MARKET",
    quoteOrderQty=str(BASELINE_AMOUNT)
)

btc_bought = Decimal("0")
cost_usdt = Decimal("0")
commission = Decimal("0")
for f in base_order.get("fills", []):
    qty = Decimal(f['qty'])
    price = Decimal(f['price'])
    fee = Decimal(f['commission'])
    btc_bought += qty
    cost_usdt += qty * price
    commission += fee
    print(f"   Fill: {qty} BTC @ {price} (fee {fee} {f['commissionAsset']})")

if btc_bought > 0:
    avg_price = cost_usdt / btc_bought
    print(f"BASELINE -> Bought {btc_bought} BTC for {cost_usdt:.2f} USDT (avg price {avg_price:.2f})")
    if commission > 0:
        print(f"   Total commission: {commission} BTC")
print("-------------------------------------")

# 2) Place limit order (dip)
filters = get_filters(SYMBOL)

dip_price = (price_now * (Decimal(1) - DIP_PERCENT))
dip_price = floor_step(dip_price, filters["tickSize"])  # adjust to tick size

dip_qty = (BASELINE_AMOUNT / dip_price)
dip_qty = floor_step(dip_qty, filters["stepSize"])  # adjust to step size

print("Placing DIP order:")
print(f"   Amount USDT : {BASELINE_AMOUNT}")
print(f"   Target price: {dip_price} USDT ({(DIP_PERCENT*100):.2f}% below current)")
print(f"   Quantity BTC: {dip_qty}")

dip_order = client.new_order(
    symbol=SYMBOL,
    side="BUY",
    type="LIMIT",
    timeInForce="GTC",
    price=str(dip_price),
    quantity=str(dip_qty)
)
print(f"DIP order placed with ID {dip_order['orderId']}")
print("-------------------------------------")


# --- Final state ---
usdt_after = get_balance("USDT")
btc_after = get_balance("BTC")

usdt_diff = usdt_after - usdt_before
btc_diff = btc_after - btc_before

print("========== FINAL SUMMARY ==========")
print(f"Final USDT balance : {usdt_after} ({usdt_diff:+f})")
print(f"Final BTC balance  : {btc_after} ({btc_diff:+f})")
print("===================================\n")

# Log to CSV
log_trade(
    action="buy_the_dip",
    symbol=SYMBOL,
    base_amount=BASELINE_AMOUNT,
    btc_qty=btc_bought,
    price=avg_price if btc_bought > 0 else None,
    fee=commission,
    dip_price=dip_price,
    dip_qty=dip_qty,
    usdt_before=usdt_before,
    usdt_after=usdt_after,
    btc_before=btc_before,
    btc_after=btc_after
)
print("Trade logged to history.csv")


# --- Telegram notification ---
from telegram_notify import send_telegram

summary = (
    "Buy-the-dip executed\n\n"
    f"Symbol: {SYMBOL}\n"
    f"Baseline: {BASELINE_AMOUNT} quote\n"
    f"Dip target: {dip_price}\n"
    f"BTC bought: {btc_bought}\n"
    f"USDT: {usdt_before} -> {usdt_after}\n"
    f"BTC:  {btc_before} -> {btc_after}\n"
)

try:
    sent = send_telegram(summary, parse_mode=None)
    print(f"Telegram sent: {sent}")
except Exception as e:
    # Do not let notifications break the investment flow
    print(f"Telegram error (ignored): {e}")
