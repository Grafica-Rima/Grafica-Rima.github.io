
import ccxt.async_support as ccxt
import pandas as pd
import asyncio
from config import Config

class DataHandler:
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',  # Perpetual futures
            }
        })
        self.symbol = Config.SYMBOL_DEFAULT
        self.timeframe = Config.BINANCE_TIMEFRAME
        self.data = pd.DataFrame()

    async def fetch_ohlcv(self, symbol=None, limit=1000):
        target_symbol = symbol if symbol else self.symbol
        # Ensure symbol is formatted correctly for CCXT if passed raw (e.g. btcusdt -> BTC/USDT)
        # But for now, we assume the frontend sends correct format or we rely on default.

        try:
            ohlcv = await self.exchange.fetch_ohlcv(target_symbol, self.timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            self.data = df
            return df
        except Exception as e:
            print(f"Error fetching data: {e}")
            return pd.DataFrame()

    async def get_latest_price(self, symbol=None):
        target_symbol = symbol if symbol else self.symbol
        try:
            ticker = await self.exchange.fetch_ticker(target_symbol)
            return ticker['last']
        except Exception as e:
            print(f"Error fetching ticker: {e}")
            return 0.0

    async def close(self):
        await self.exchange.close()
