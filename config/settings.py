"""
Configuration settings for the Binance BTC DCA bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Environment Configuration
USE_TESTNET = os.getenv("USE_TESTNET", "false").lower() == "true"
BASE_URL = "https://testnet.binance.vision" if USE_TESTNET else None

# API Configuration
if USE_TESTNET:
    API_KEY = os.getenv("BINANCE_API_KEY_TEST")
    API_SECRET = os.getenv("BINANCE_API_SECRET_TEST")
else:
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SECRET = os.getenv("BINANCE_API_SECRET")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Trading Configuration
TRADING_PAIR = "BTCEUR"
BASE_CURRENCY = "EUR"
TARGET_CURRENCY = "BTC"

# DCA Settings
SIMPLE_DCA_AMOUNT = 10.0  # EUR
MIN_BALANCE_REQUIRED = 10.0  # EUR

# Buy the Dip Settings
BUY_THE_DIP_AMOUNTS = {
    "small_dip": 20.0,    # EUR
    "medium_dip": 50.0,   # EUR
    "large_dip": 100.0    # EUR
}

# Price thresholds for buy-the-dip strategy (percentage drops)
DIP_THRESHOLDS = {
    "small_dip": 5.0,     # 5% drop
    "medium_dip": 10.0,   # 10% drop
    "large_dip": 20.0     # 20% drop
}
