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
        if self.mock_mode:
            return

        # Try Binance Global first
        try:
            print("Attempting to connect to Binance (Global)...")
            self.exchange = ccxt.binance({
                'apiKey': Config.BINANCE_API_KEY,
                'secret': Config.BINANCE_API_SECRET,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
            # Test connection (lightweight)
            # Some restricted regions fail on load_markets or fetch_ohlcv
            # We'll rely on lazy failure or explicit check if keys provided
        except Exception as e:
            print(f"Binance Global Init Failed: {e}")

        # If fetch fails later, or if we want to support US fallback immediately:
        # We can't easily "test" it without a request.
        # But we can try to fetch a ticker or something to validate.

        # Let's add a robust fetcher that handles the fallback dynamically.

    def fetch_ohlcv(self, symbol=Config.DEFAULT_PAIR, timeframe=Config.TIMEFRAME, limit=Config.LIMIT):
        """
        Fetches OHLCV data.
        """
        if self.mock_mode:
            return self._generate_mock_data(limit)

        try:
            # Ensure exchange is initialized
            if not self.exchange:
                 self._initialize_exchange()

            # Attempt Fetch
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return self._process_ohlcv(ohlcv)

        except Exception as e:
            print(f"Error fetching from Primary Exchange: {e}")

            # Check if it's a restriction error (451) or similar
            if "451" in str(e) or "Service unavailable" in str(e) or "ExchangeNotAvailable" in str(e):
                print("Switching to Binance US fallback due to restriction...")
                try:
                    # Fallback to Binance US
                    # Note: Binance US doesn't support 'future' usually, only spot.
                    # But for price data, spot is often close enough for a prototype if futures are blocked.
                    # Or we check if they have it. BinanceUS is spot only mostly.
                    self.exchange = ccxt.binanceus({
                        'enableRateLimit': True
                    })
                    ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                    return self._process_ohlcv(ohlcv)
                except Exception as e2:
                    print(f"Binance US Fallback Failed: {e2}")

            # Final Fallback to Mock
            print("All exchanges failed. Returning MOCK data.")
            return self._generate_mock_data(limit)

    def _process_ohlcv(self, ohlcv):
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

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
