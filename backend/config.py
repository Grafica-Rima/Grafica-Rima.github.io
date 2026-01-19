
class Config:
    BINANCE_TIMEFRAME = '5m'
    SYMBOL_DEFAULT = 'BTC/USDT'
    # Simulation mode to avoid actual ordering, but we treat it as "Real Money" readiness in logic.
    # In a real scenario, API keys would be here or in env vars.
    # Since we are just generating signals, we don't strictly need API keys for public data on Binance.
    # However, for robustness, we structure it to accept them.
    API_KEY = None
    API_SECRET = None

    # Strategy Config
    RSI_PERIOD = 14
    MA_FAST = 50
    MA_SLOW = 200
    VOLUME_MA_PERIOD = 20

    # Risk Management
    RISK_REWARD_RATIO = 2.0  # Target at least 1:2
    SL_ATR_MULTIPLIER = 1.5
    TP_ATR_MULTIPLIER = 3.0
