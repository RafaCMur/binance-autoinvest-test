"""
Configuration settings for the Binance BTC DCA bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Environment Configuration
USE_TESTNET = os.getenv("USE_TESTNET", "true").lower() == "true"
BASE_URL = "https://testnet.binance.vision" if USE_TESTNET else "https://api.binance.com"

# API Configuration
if USE_TESTNET:
    API_KEY = os.getenv("BINANCE_API_KEY_TEST")
    API_SECRET = os.getenv("BINANCE_API_SECRET_TEST")
else:
    API_KEY = os.getenv("BINANCE_API_KEY")
    API_SECRET = os.getenv("BINANCE_API_SECRET")

# Trading Configuration
TRADING_PAIR = "BTCUSDT" if USE_TESTNET else "BTCEUR"
BASE_CURRENCY = "USDT" if USE_TESTNET else "EUR"
TARGET_CURRENCY = "BTC"

# Simple DCA Settings
SIMPLE_DCA_AMOUNT = 10.0  # USDT for testnet, EUR for mainnet
MIN_BALANCE_REQUIRED = 10.0  # USDT for testnet, EUR for mainnet

# Buy The Dip Settings
BASELINE_AMOUNT = 10.0  # USDT for testnet, EUR for mainnet
MIN_DIP_PERCENT = 0.02  # minimum -2% dip level
MAX_DIP_PERCENT = 0.15  # maximum -15% dip level
DIP_INCREMENT = 0.01    # 1% increment between dip levels
