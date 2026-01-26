import os

class Config:
    # Exchange Settings
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

    # Trading Settings
    DEFAULT_PAIR = "BTC/USDT"
    TIMEFRAME = "5m"
    LIMIT = 100  # Number of candles to fetch for analysis

    # App Settings
    # If True, generates random data instead of connecting to Binance
    # Set to True by default to avoid API errors in sandbox unless user provides keys
    MOCK_MODE = True

    # Strategy Parameters
    RSI_PERIOD = 14
    EMA_FAST = 9
    EMA_SLOW = 21
    EMA_TREND = 200

    # Risk Management
    LEVERAGE = 10
    RISK_REWARD_RATIO = 2.0  # Minimum 1:2
