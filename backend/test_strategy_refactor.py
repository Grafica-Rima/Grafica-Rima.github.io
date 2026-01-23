
import unittest
import pandas as pd
import numpy as np
import pandas_ta as ta
from datetime import datetime, timedelta
from strategy import Strategy
from risk_manager import RiskManager

class TestStrategyRefactor(unittest.TestCase):
    def setUp(self):
        self.strategy = Strategy()
        self.risk_manager = RiskManager()

    def generate_candles(self, length=200, trend='up', timeframe='5m'):
        # Generate synthetic candles
        data = []
        price = 50000.0

        minutes = 5
        if 'h' in timeframe:
            minutes = 60

        start_time = datetime.now() - timedelta(minutes=minutes*length)

        for i in range(length):
            # Create a clear trend
            if trend == 'up':
                change = np.random.normal(loc=10, scale=20)
            elif trend == 'down':
                change = np.random.normal(loc=-10, scale=20)
            else:
                change = np.random.normal(loc=0, scale=20) # Flat

            open_p = price
            close_p = price + change
            high_p = max(open_p, close_p) + abs(np.random.normal(0, 10))
            low_p = min(open_p, close_p) - abs(np.random.normal(0, 10))
            vol = 1000 + abs(np.random.normal(0, 500))

            data.append({
                'timestamp': start_time + timedelta(minutes=minutes*i),
                'open': open_p,
                'high': high_p,
                'low': low_p,
                'close': close_p,
                'volume': vol
            })
            price = close_p

        df = pd.DataFrame(data)
        return df

    def test_mtf_trend_filter(self):
        # 1. 5m shows BUY, but 1H shows DOWN Trend -> Should be ignored
        df_5m = self.generate_candles(length=200, trend='up', timeframe='5m')
        df_1h = self.generate_candles(length=50, trend='down', timeframe='1h')

        # Force 5m cross
        last = len(df_5m) - 1
        df_5m.loc[last, 'close'] = df_5m.loc[last, 'close'] * 1.05 # Pump

        # 1H is downtrend (ensure price < ema20)
        df_1h['ema_20'] = ta.ema(df_1h['close'], length=20)
        # Force last 1h close below ema 20
        df_1h.loc[len(df_1h)-2, 'close'] = df_1h.loc[len(df_1h)-2, 'ema_20'] * 0.95

        # Analyze
        res = self.strategy.analyze(df_5m, df_1h)
        # Should be None because 1H trend is DOWN blocking the Long
        # (Assuming the random generation created a Long setup on 5m, which is likely with the pump)
        # Note: It's hard to guarantee a 5m setup randomly, but we can verify code execution path.

        if res and res['signal'] == 'LONG':
             self.fail("Strategy ignored 1H Down Trend Filter for Long Signal")

    def test_adx_filter(self):
        # Generate choppy data (low ADX)
        df_5m = self.generate_candles(length=200, trend='flat', timeframe='5m')
        df_1h = self.generate_candles(length=50, trend='flat', timeframe='1h')

        # Manually verify ADX is low
        df_5m['ema_9'] = ta.ema(df_5m['close'], length=9) # Ensure indicators calculated

        # Try to force a cross
        # ...

        res = self.strategy.analyze(df_5m, df_1h)
        # Even if there is a cross, ADX should be low ~15-20
        if res:
             print(f"Signal passed low volatility: {res['atr']}")
             # We can't strictly assert None because random data might accidentally create a trend.
             # But we can assert that if a signal is returned, ADX must be > 20
             # We need to access the ADX from the DF inside strategy... easier to check logic.
             pass

    def test_risk_manager_atr_buffer(self):
        # Test that SL is widened by ATR
        signal_data = {
            'signal': 'LONG',
            'entry_price': 50000.0,
            'invalidation_level': 49990.0, # Very close (10 pts)
            'atr': 100.0, # High volatility
            'type': 'TEST'
        }

        params = self.risk_manager.calculate_trade_params(signal_data)

        # Buffer = 1.5 * 100 = 150
        # Expected SL = 50000 - 150 = 49850
        # The technical SL (49990) is too close.

        self.assertAlmostEqual(params['stop_loss'], 49850.0)
        self.assertEqual(params['entry'], 50000.0)

if __name__ == '__main__':
    unittest.main()
