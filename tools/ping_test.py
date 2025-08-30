from binance.spot import Spot
from dotenv import load_dotenv
import os

load_dotenv()

USE_TESTNET = os.getenv("USE_TESTNET", "true").lower() == "true"
BASE_URL = "https://testnet.binance.vision" if USE_TESTNET else None

client = Spot(
    api_key=os.getenv("BINANCE_API_KEY_TEST"),
    api_secret=os.getenv("BINANCE_API_SECRET_TEST"),
    base_url=BASE_URL
)

print("Ping:", client.ping())
