import ccxt.pro as ccxtpro
import ccxt.async_support as ccxt_async
import ccxt
import pandas as pd
import asyncio
from config import EXCHANGE_ID, TIMEFRAME

class DataHandler:
    def __init__(self):
        # We will keep a persistent async exchange instance
        self.exchange_async = getattr(ccxt_async, EXCHANGE_ID)({
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
        self.symbol = None

    async def close_exchange(self):
        if self.exchange_async:
            await self.exchange_async.close()

    def set_symbol(self, symbol):
        self.symbol = symbol.upper()

    async def fetch_ohlcv(self, limit=100):
        if not self.symbol:
            return None

        try:
            ohlcv = await self.exchange_async.fetch_ohlcv(self.symbol, TIMEFRAME, limit=limit)

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception as e:
            print(f"Error fetching OHLCV: {e}")
            return None

    async def fetch_current_price(self):
        if not self.symbol:
            return 0.0
        try:
            ticker = await self.exchange_async.fetch_ticker(self.symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error fetching price: {e}")
            return 0.0
