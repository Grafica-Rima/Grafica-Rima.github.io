
# API Configuration
BINANCE_API_KEY = ""  # Not needed for public data, but good to have variable ready
BINANCE_SECRET_KEY = ""
DEFAULT_TIMEFRAME = "5m"
DEFAULT_PAIR = "BTC/USDT"

# Risk Management
# Stop Loss and Take Profit percentages can be dynamic, but here are some defaults if needed.
# The strategy will likely calculate these based on the pattern height/Fib levels.
MAX_RISK_PER_TRADE = 0.01  # 1% risk per trade example

# Websocket
SOCKET_SERVER_URL = "http://localhost:8000"
