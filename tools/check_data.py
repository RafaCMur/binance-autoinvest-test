from binance.spot import Spot
from dotenv import load_dotenv
import os

# Cargar las variables del archivo .env
load_dotenv()

# Seleccionar endpoint (testnet o mainnet)
USE_TESTNET = os.getenv("USE_TESTNET", "true").lower() == "true"
BASE_URL = "https://testnet.binance.vision" if USE_TESTNET else None

# Cliente Binance
client = Spot(
    api_key=os.getenv("BINANCE_API_KEY_TEST"),
    api_secret=os.getenv("BINANCE_API_SECRET_TEST"),
    base_url=BASE_URL
)

# 1) Comprobar conexión
print("Ping:", client.ping())

# 2) Precio de BTC/EUR
btc_price = client.ticker_price("BTCEUR")
print("Precio BTC/EUR:", btc_price["price"])

# 3) Mostrar saldo EUR en cuenta Spot
account = client.account()
eur_balance = next((b for b in account["balances"] if b["asset"] == "EUR"), None)

if eur_balance:
    print("Saldo EUR disponible:", eur_balance["free"])
else:
    print("No se encontró saldo EUR en la cuenta.")
