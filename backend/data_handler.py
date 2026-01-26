
import ccxt.async_support as ccxt
import asyncio
import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
from config import DEFAULT_TIMEFRAME

class DataHandler:
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'future',
            }
        })
        self.symbol = None
        self.default_timeframe = DEFAULT_TIMEFRAME
        self.mock_mode = False
        self.mock_price = 50000.0
        self.mock_data = []

    async def initialize(self):
        try:
            await self.exchange.load_markets()
        except Exception as e:
            if "451" in str(e) or "Service unavailable" in str(e):
                print("Warning: Binance API restricted (Error 451). Switching to MOCK MODE.")
                self.mock_mode = True
                self.symbol = "BTC/USDT" # Default for mock
            else:
                print(f"Error initializing exchange: {e}")
                self.mock_mode = True

    async def close(self):
        await self.exchange.close()

    async def fetch_candles(self, symbol, timeframe=None, limit=1000):
        """
        Fetches OHLCV data.
        timeframe: Defaults to DEFAULT_TIMEFRAME (5m) if None.
        """
        tf = timeframe if timeframe else self.default_timeframe

        if not self.exchange.markets and not self.mock_mode:
            await self.initialize()

        if self.mock_mode:
            return self._generate_mock_candles(limit, tf)

        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, tf, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching candles ({tf}): {e}")
            return pd.DataFrame()

    async def fetch_current_price(self, symbol):
        if not self.exchange.markets and not self.mock_mode:
            await self.initialize()

        if self.mock_mode:
            # Random walk
            change = random.uniform(-50, 50)
            self.mock_price += change
            return self.mock_price

        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error fetching price: {e}")
            return None

    async def validate_symbol(self, symbol):
        if self.mock_mode:
            return symbol.upper() if symbol else "BTC/USDT"

        if not self.exchange.markets:
            await self.initialize()

        clean_symbol = symbol.upper().replace('.P', '').replace('p', '')
        if '/' not in clean_symbol:
            if clean_symbol.endswith('USDT'):
                clean_symbol = clean_symbol[:-4] + '/USDT'
            elif clean_symbol.endswith('BUSD'):
                clean_symbol = clean_symbol[:-4] + '/BUSD'

        if clean_symbol in self.exchange.markets:
            return clean_symbol
        return None

    def _generate_mock_candles(self, limit, timeframe):
        # Generate synthetic OHLCV data for testing
        # Adjust interval based on timeframe string (basic parsing)
        minutes = 5
        if 'h' in timeframe:
            minutes = int(timeframe.replace('h', '')) * 60
        elif 'm' in timeframe:
            minutes = int(timeframe.replace('m', ''))

        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=minutes*limit)

        timestamps = []
        current = start_time
        for _ in range(limit):
            timestamps.append(current)
            current += timedelta(minutes=minutes)

        # Random walk price generation
        price = 50000.0
        data = []
        for ts in timestamps:
            open_p = price
            # More volatility for higher timeframes
            volatility = 100 if minutes <= 15 else 300

            close_p = price + random.uniform(-volatility, volatility)
            high_p = max(open_p, close_p) + random.uniform(0, volatility/2)
            low_p = min(open_p, close_p) - random.uniform(0, volatility/2)
            volume = random.uniform(100, 1000)
            data.append([ts, open_p, high_p, low_p, close_p, volume])
            price = close_p

        df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        return df
