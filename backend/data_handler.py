import ccxt
import pandas as pd
import pandas_ta as ta
import numpy as np
from config import Config

class DataHandler:
    def __init__(self):
        self.exchange = None
        self.mock_mode = Config.MOCK_MODE
        self._initialize_exchange()

    def _initialize_exchange(self):
        if self.mock_mode:
            return

        try:
            print("Attempting to connect to Binance (Global)...")
            self.exchange = ccxt.binance({
                'apiKey': Config.BINANCE_API_KEY,
                'secret': Config.BINANCE_API_SECRET,
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}
            })
        except Exception as e:
            print(f"Binance Global Init Failed: {e}")

    def fetch_ohlcv(self, symbol=Config.DEFAULT_PAIR, timeframe=Config.TIMEFRAME, limit=Config.LIMIT):
        """
        Fetches OHLCV data.
        Returns None if data unavailable. NO Mock fallback on error.
        """
        if self.mock_mode:
            return self._generate_mock_data(limit)

        try:
            if not self.exchange:
                 self._initialize_exchange()

            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return self._process_ohlcv(ohlcv)

        except Exception as e:
            print(f"Error fetching from Primary Exchange: {e}")

            # 451 Handling (Geo-restriction)
            if "451" in str(e) or "Service unavailable" in str(e) or "ExchangeNotAvailable" in str(e):
                print("Switching to Binance US fallback due to restriction...")
                try:
                    self.exchange = ccxt.binanceus({'enableRateLimit': True})
                    ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
                    return self._process_ohlcv(ohlcv)
                except Exception as e2:
                    print(f"Binance US Fallback Failed: {e2}")

            # CRITICAL: Do NOT return Mock data here. Return None to signal system failure.
            print("⚠️ MARKET DATA UNAVAILABLE ⚠️")
            return None

    def _process_ohlcv(self, ohlcv):
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df

    def add_indicators(self, df):
        """Adds essential indicators for Strategy/Risk (ATR)"""
        if df is None or df.empty: return df

        # ATR for Risk Management
        df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)

        # ADX for Chop Filter
        adx = ta.adx(df['high'], df['low'], df['close'], length=14)
        if adx is not None and not adx.empty:
            df['ADX'] = adx['ADX_14']

        return df

    def _generate_mock_data(self, limit):
        # Keeps mock for explicit MOCK_MODE, but not for error fallback
        dates = pd.date_range(end=pd.Timestamp.now(), periods=limit, freq=Config.TIMEFRAME.replace('m', 'min'))
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
            'timestamp': dates, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume
        })
        return self.add_indicators(df)
