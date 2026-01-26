import ccxt
import pandas as pd
import numpy as np
import time
from backend.config import Config

class DataHandler:
    def __init__(self):
        self.exchange = None
        self.mock_mode = Config.MOCK_MODE
        self._initialize_exchange()

    def _initialize_exchange(self):
        if not self.mock_mode:
            try:
                self.exchange = ccxt.binance({
                    'apiKey': Config.BINANCE_API_KEY,
                    'secret': Config.BINANCE_API_SECRET,
                    'enableRateLimit': True,
                    'options': {
                        'defaultType': 'future'
                    }
                })
                # Check connectivity (optional, but good for fail-fast)
                # self.exchange.load_markets()
            except Exception as e:
                print(f"Error initializing exchange: {e}")
                print("Switching to MOCK MODE.")
                self.mock_mode = True

    def fetch_ohlcv(self, symbol=Config.DEFAULT_PAIR, timeframe=Config.TIMEFRAME, limit=Config.LIMIT):
        """
        Fetches OHLCV data.
        Note: This uses synchronous CCXT. In a high-perf async app, consider ccxt.async_support.
        """
        if self.mock_mode:
            return self._generate_mock_data(limit)

        try:
            # Standardizing symbol for Binance Futures if needed
            # But usually pair search like "BTC/USDT" works.
            # If user types 'btcusdt.p', we might need to clean it up in the App level or here.
            # For now, assume correct format is passed or handled.

            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df

        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            # If fetch fails (e.g. 451 error), fallback to mock or empty
            return self._generate_mock_data(limit)

    def _generate_mock_data(self, limit):
        # Generate a random walk
        dates = pd.date_range(end=pd.Timestamp.now(), periods=limit, freq=Config.TIMEFRAME.replace('m', 'min'))

        # Random price movement
        base_price = 50000
        volatility = 0.002

        close = [base_price]
        for _ in range(limit - 1):
            change = np.random.normal(0, base_price * volatility)
            close.append(close[-1] + change)

        close = np.array(close)
        high = close + np.random.rand(limit) * (base_price * 0.001)
        low = close - np.random.rand(limit) * (base_price * 0.001)
        open_ = np.roll(close, 1)
        open_[0] = base_price
        volume = np.random.randint(100, 1000, limit) * 1.0

        df = pd.DataFrame({
            'timestamp': dates,
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
        return df
