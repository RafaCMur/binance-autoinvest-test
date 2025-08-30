from binance.spot import Spot
from dotenv import load_dotenv
from decimal import Decimal, ROUND_DOWN, getcontext
import os
from datetime import datetime, timezone
from logger_csv import log_trade

load_dotenv()
getcontext().prec = 28

USE_TESTNET = os.getenv("USE_TESTNET", "false").lower() == "true"
BASE_URL = "https://testnet.binance.vision" if USE_TESTNET else None

# Use mainnet keys by default, fallback to test keys if specified
if USE_TESTNET:
    API_KEY = os.getenv("BINANCE_API_KEY_TEST")
    API_SECRET = os.getenv("BINANCE_API_SECRET_TEST")
else:
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SECRET = os.getenv("BINANCE_API_SECRET")

client = Spot(api_key=API_KEY, api_secret=API_SECRET, base_url=BASE_URL)

# ===== Config =====
SYMBOL = "BTCEUR" if not USE_TESTNET else "BTCUSDT"
BASE_CURRENCY = "EUR" if not USE_TESTNET else "USDT"
BASELINE_AMOUNT = Decimal("10.00")  # baseline buy amount in base currency
MIN_DIP_PERCENT = Decimal("0.02")   # minimum -2% dip level
MAX_DIP_PERCENT = Decimal("0.08")   # maximum -8% dip level
MAX_DAILY_SPEND = Decimal("50.00")  # safety limit for real money

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

def calculate_dynamic_dip_percent() -> Decimal:
    """Calculate dip percentage based on recent volatility"""
    try:
        # Get 24h price change percentage
        ticker = client.ticker_24hr(symbol=SYMBOL)
        price_change_percent = abs(Decimal(ticker['priceChangePercent']))
        
        # Scale dip percentage based on volatility
        # Low volatility (0-2%): use minimum dip (2%)
        # High volatility (8%+): use maximum dip (8%)
        if price_change_percent <= Decimal("2"):
            return MIN_DIP_PERCENT
        elif price_change_percent >= Decimal("8"):
            return MAX_DIP_PERCENT
        else:
            # Linear scaling between min and max
            volatility_ratio = (price_change_percent - Decimal("2")) / Decimal("6")
            dip_range = MAX_DIP_PERCENT - MIN_DIP_PERCENT
            return MIN_DIP_PERCENT + (volatility_ratio * dip_range)
    except Exception as e:
        print(f"Error calculating dynamic dip: {e}, using minimum dip")
        return MIN_DIP_PERCENT

# ===== Script =====
print("\n========== START EXECUTION ==========")
print("Datetime (UTC):", datetime.now(timezone.utc).isoformat())
print("=====================================")

base_before = get_balance(BASE_CURRENCY)
btc_before = get_balance("BTC")
print(f"Initial {BASE_CURRENCY} balance : {base_before}")
print(f"Initial BTC balance  : {btc_before}")

# Safety check for real money
if not USE_TESTNET:
    if base_before < BASELINE_AMOUNT * 2:
        raise Exception(f"Insufficient {BASE_CURRENCY} balance. Need at least {BASELINE_AMOUNT * 2} for safety")
    if BASELINE_AMOUNT > MAX_DAILY_SPEND:
        raise Exception(f"Baseline amount {BASELINE_AMOUNT} exceeds daily limit {MAX_DAILY_SPEND}")
print("-------------------------------------")

# Cancel old limit orders
cancel_old_orders()

# Current price and dynamic dip calculation
price_now = Decimal(client.ticker_price(SYMBOL)["price"])
dip_percent = calculate_dynamic_dip_percent()
print(f"Current {SYMBOL} price: {price_now} {BASE_CURRENCY}")
print(f"24h volatility-based dip percentage: {(dip_percent*100):.1f}%\n")

# 1) Baseline market buy
print(f"Executing BASELINE market buy of {BASELINE_AMOUNT} {BASE_CURRENCY}...")
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
    cost_usdt += qty * price  # cost in base currency
    commission += fee
    print(f"   Fill: {qty} BTC @ {price} (fee {fee} {f['commissionAsset']})")

if btc_bought > 0:
    avg_price = cost_usdt / btc_bought
    print(f"BASELINE -> Bought {btc_bought} BTC for {cost_usdt:.2f} {BASE_CURRENCY} (avg price {avg_price:.2f})")
    if commission > 0:
        print(f"   Total commission: {commission} BTC")
print("-------------------------------------")

# Get trading filters
filters = get_filters(SYMBOL)

# 2) Place limit order for the dip
print(f"Placing LIMIT order for the dip...")
dip_price = (price_now * (Decimal(1) - dip_percent))
dip_price = floor_step(dip_price, filters["tickSize"])
dip_qty = (BASELINE_AMOUNT / dip_price)
dip_qty = floor_step(dip_qty, filters["stepSize"])  # adjust to step size

print("Placing DIP order:")
print(f"   Amount {BASE_CURRENCY} : {BASELINE_AMOUNT}")
print(f"   Target price: {dip_price} {BASE_CURRENCY} ({(dip_percent*100):.2f}% below current)")
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
base_after = get_balance(BASE_CURRENCY)
btc_after = get_balance("BTC")

base_diff = base_after - base_before
btc_diff = btc_after - btc_before

print("========== FINAL SUMMARY ==========")
print(f"Final {BASE_CURRENCY} balance : {base_after} ({base_diff:+f})")
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
    base_before=base_before,
    base_after=base_after,
    btc_before=btc_before,
    btc_after=btc_after,
    base_currency=BASE_CURRENCY
)
print("Trade logged to history.csv")


# --- Telegram notification ---
from telegram_notify import send_telegram

summary = (
    f"Bitcoin Buy Order Executed {'(TESTNET)' if USE_TESTNET else '(MAINNET)'}\n\n"
    f"Trading Pair: {SYMBOL}\n"
    f"Market Buy: {BASELINE_AMOUNT} {BASE_CURRENCY}\n"
    f"Bitcoin Purchased: {btc_bought}\n"
    f"Average Price: {avg_price if btc_bought > 0 else 'N/A'} {BASE_CURRENCY}\n"
    f"Trading Fee: {commission} BTC\n"
    f"Limit Order Price: {dip_price} {BASE_CURRENCY} (-{(dip_percent*100):.1f}%)\n"
    f"Limit Order Quantity: {dip_qty} BTC\n\n"
    f"{BASE_CURRENCY} Balance: {base_before} -> {base_after} ({base_after - base_before:+.2f})\n"
    f"BTC Balance: {btc_before} -> {btc_after} ({btc_after - btc_before:+.8f})\n\n"
    f"Strategy: Market buy + limit order placed for next dip\n"
    f"Executed: {datetime.now(timezone.utc).strftime('%d/%m/%Y %H:%M:%S')} UTC"
)

try:
    sent = send_telegram(summary, parse_mode=None)
    print(f"Telegram sent: {sent}")
except Exception as e:
    # Do not let notifications break the investment flow
    print(f"Telegram error (ignored): {e}")
