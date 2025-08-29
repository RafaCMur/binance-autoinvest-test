from binance.spot import Spot
from dotenv import load_dotenv
import os
from decimal import Decimal, ROUND_DOWN

load_dotenv()

USE_TESTNET = os.getenv("USE_TESTNET", "true").lower() == "true"
BASE_URL = "https://testnet.binance.vision" if USE_TESTNET else None

client = Spot(
    api_key=os.getenv("BINANCE_API_KEY_TEST"),
    api_secret=os.getenv("BINANCE_API_SECRET_TEST"),
    base_url=BASE_URL
)

def get_balance(asset: str) -> Decimal:
    acc = client.account()
    bal = next((b for b in acc["balances"] if b["asset"] == asset), None)
    return Decimal(bal["free"]) if bal else Decimal("0")

print("========== ESTADO INICIAL ==========")
usdt_before = get_balance("USDT")
btc_before = get_balance("BTC")
print(f"USDT disponible : {usdt_before}")
print(f"BTC disponible  : {btc_before}")
print("====================================\n")

# --- mínimo notional ---
info = client.exchange_info(symbol="BTCUSDT")["symbols"][0]["filters"]
min_notional = float(next(f["minNotional"] for f in info if f["filterType"] in ("NOTIONAL","MIN_NOTIONAL")))
print(f"Mínimo notional permitido BTCUSDT: {min_notional} USDT")

# --- monto a invertir (mínimo 10 USDT normalmente) ---
amount = Decimal("10.00").quantize(Decimal("0.01"), rounding=ROUND_DOWN)
print(f"Invirtiendo ahora: {amount} USDT en BTC\n")

# --- ejecutar orden ---
order = client.new_order(
    symbol="BTCUSDT",
    side="BUY",
    type="MARKET",
    quoteOrderQty=str(amount)
)

print("========== ORDEN EJECUTADA ==========")
print(f"ID Orden        : {order['orderId']}")
print(f"Símbolo         : {order['symbol']}")
print(f"Estado          : {order['status']}")
print(f"Cantidad BTC    : {order['executedQty']}")
print(f"Coste en USDT   : {order['cummulativeQuoteQty']}")
if order.get("fills"):
    fill = order["fills"][0]
    print(f"Precio de fill  : {fill['price']}")
print("====================================\n")

# --- mostrar saldos después ---
usdt_after = get_balance("USDT")
btc_after = get_balance("BTC")

print("========== ESTADO FINAL ==========")
print(f"USDT disponible : {usdt_after}")
print(f"BTC disponible  : {btc_after}")
print("==================================")
