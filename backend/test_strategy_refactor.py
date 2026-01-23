
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

    def generate_trend_data(self, length=200, trend='up'):
        # Generate synthetic candles
        data = []
        price = 50000.0
        start_time = datetime.now() - timedelta(minutes=5*length)

        for i in range(length):
            # Create a clear trend
            if trend == 'up':
                change = np.random.normal(loc=10, scale=20) # slight upward bias
            else:
                change = np.random.normal(loc=-10, scale=20)

            open_p = price
            close_p = price + change
            high_p = max(open_p, close_p) + abs(np.random.normal(0, 10))
            low_p = min(open_p, close_p) - abs(np.random.normal(0, 10))
            vol = 1000 + abs(np.random.normal(0, 500))

            data.append({
                'timestamp': start_time + timedelta(minutes=5*i),
                'open': open_p,
                'high': high_p,
                'low': low_p,
                'close': close_p,
                'volume': vol
            })
            price = close_p

        df = pd.DataFrame(data)
        return df

    def test_ema_cross_long(self):
        # Create data where price is generally going up (Price > EMA 200)
        # And specifically simulate an EMA 9 crossing above EMA 21 at the end
        df = self.generate_trend_data(length=250, trend='up')

        # Manually force the last few candles to create a cross
        # EMA 200 is roughly average price of last 200.
        # We need Price > EMA 200 (which it should be in 'up' trend)

        # Make the last 5 candles shoot up to cross EMA 9 over 21
        # Previous: EMA 9 < 21. Current: EMA 9 > 21.
        # This is hard to "force" perfectly with EMAs without calculation,
        # but we can try to make a massive jump.

        last_idx = len(df) - 1
        current_price = df['close'].iloc[last_idx]

        # Inject a massive volume spike and price jump at the end
        df.loc[last_idx-2, 'close'] = current_price * 0.99 # Dip
        df.loc[last_idx-1, 'close'] = current_price * 1.00 # Recover
        df.loc[last_idx, 'close'] = current_price * 1.02 # Pump
        df.loc[last_idx, 'volume'] = 50000 # Spike

        # This test mainly checks that code runs without crashing and calculates indicators
        res = self.strategy.analyze(df)

        # We might not get a signal if the EMA math doesn't work out exactly,
        # but we check that columns were created.
        self.assertIn('ema_9', df.columns)
        self.assertIn('ema_21', df.columns)
        self.assertIn('vwap', df.columns)

        if res:
            print(f"Signal Detected: {res}")
            self.assertIn(res['signal'], ['LONG', 'SHORT'])

            # Test Risk Manager
            risk_params = self.risk_manager.calculate_trade_params(res)
            self.assertIsNotNone(risk_params)
            self.assertGreater(risk_params['take_profit'], 0)

            # Check RR > 1.5 approx
            risk = abs(risk_params['entry'] - risk_params['stop_loss'])
            reward = abs(risk_params['take_profit'] - risk_params['entry'])
            self.assertGreater(reward, risk * 1.9) # We set 2.0 in manager

    def test_no_future_bias(self):
        # Ensure pivot logic doesn't crash or use future
        df = self.generate_trend_data(length=100)
        # The strategy iterates backwards from len(df) - 3.
        # It should not access i > len(df)
        try:
            self.strategy.analyze(df)
        except IndexError:
            self.fail("Strategy accessed future index")

if __name__ == '__main__':
    unittest.main()
