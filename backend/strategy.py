import pandas as pd
import pandas_ta as ta
import numpy as np
from scipy.signal import argrelextrema
from backend.config import Config

class Strategy:
    def __init__(self):
        self.ema_fast = Config.EMA_FAST
        self.ema_slow = Config.EMA_SLOW
        self.ema_trend = Config.EMA_TREND

    def analyze(self, df):
        """
        Analyzes the DataFrame and returns a signal.
        df: DataFrame with at least ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        """
        if len(df) < self.ema_trend + 10:
            return "NEUTRAL"

        # 1. Indicators
        df['EMA_FAST'] = ta.ema(df['close'], length=self.ema_fast)
        df['EMA_SLOW'] = ta.ema(df['close'], length=self.ema_slow)
        df['EMA_TREND'] = ta.ema(df['close'], length=self.ema_trend)

        # Volume Moving Average
        df['VOL_MA'] = ta.sma(df['volume'], length=20)

        # Get latest closed candle (iloc[-2] because iloc[-1] might be open/developing if fetched real-time)
        # However, user said "When a new candle opens, observe the LAST CLOSED candle".
        # So we assume df includes the last closed candle at the end, or we handle the logic.
        # Usually, fetched data includes the latest one. If we fetch 'limit=100', the last row is the latest.
        # If the latest is still open, we should look at -2.
        # For simplicity, we assume we are analyzing the latest available COMPLETE data point.
        # If we fetch continuously, we usually ignore the last row if it's the current incomplete candle.
        # Let's assume the caller handles stripping the incomplete candle, OR we just look at iloc[-1] assuming it's the target.
        # User: "When a new candle opens, ... observe [the] last closed candle"

        current_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]

        signal = "NEUTRAL"

        # 2. Pattern & Fib Analysis
        is_fib_support = self._check_fibonacci(df, 'support')
        is_fib_resistance = self._check_fibonacci(df, 'resistance')

        pattern_signal = self._detect_pattern_breakout(df)

        # 3. Moving Average Logic
        # Bullish: Fast > Slow & Price > Trend
        trend_bullish = current_candle['close'] > current_candle['EMA_TREND']
        trend_bearish = current_candle['close'] < current_candle['EMA_TREND']

        ma_cross_up = (prev_candle['EMA_FAST'] <= prev_candle['EMA_SLOW']) and (current_candle['EMA_FAST'] > current_candle['EMA_SLOW'])
        ma_cross_down = (prev_candle['EMA_FAST'] >= prev_candle['EMA_SLOW']) and (current_candle['EMA_FAST'] < current_candle['EMA_SLOW'])

        # 4. Volume Confirmation
        # Check LAST CLOSED candle for high volume (confirming the move started)
        # OR check current candle if it is already exceeding average (strong impulse)
        vol_increasing = (prev_candle['volume'] > prev_candle['VOL_MA']) or \
                         (current_candle['volume'] > current_candle['VOL_MA'])

        # 5. Signal Combination

        # LONG CRITERIA
        if trend_bullish:
            if (pattern_signal == "LONG" or is_fib_support or ma_cross_up) and vol_increasing:
                signal = "LONG"

        # SHORT CRITERIA
        elif trend_bearish:
            if (pattern_signal == "SHORT" or is_fib_resistance or ma_cross_down) and vol_increasing:
                signal = "SHORT"

        return signal

    def _check_fibonacci(self, df, mode):
        # Identify significant Swing High/Low in the last 50 candles
        window = 50
        subset = df.iloc[-window:]
        max_price = subset['high'].max()
        min_price = subset['low'].min()

        diff = max_price - min_price
        if diff == 0: return False

        # Fib Levels
        fib_618 = min_price + (diff * 0.618)
        fib_382 = min_price + (diff * 0.382)

        current_price = df.iloc[-1]['close']

        # Tolerance usually 0.05%
        tolerance = current_price * 0.0005

        if mode == 'support':
            # Price bouncing off 0.618 retracement in an uptrend context?
            # Or simplified: is price near a key fib level that acts as support?
            # If we are simply looking for "near 0.618"
            if abs(current_price - fib_618) < tolerance:
                return True
        elif mode == 'resistance':
            if abs(current_price - fib_382) < tolerance: # 382 from bottom is 618 from top
                return True

        return False

    def _detect_pattern_breakout(self, df):
        """
        Simplified pattern detection using slope of recent pivots.
        Returns "LONG", "SHORT", or None
        """
        # Find pivots
        n = 5 # Neighbor comparison
        df['min'] = df.iloc[argrelextrema(df.close.values, np.less_equal, order=n)[0]]['close']
        df['max'] = df.iloc[argrelextrema(df.close.values, np.greater_equal, order=n)[0]]['close']

        last_highs = df['max'].dropna().iloc[-3:]
        last_lows = df['min'].dropna().iloc[-3:]

        if len(last_highs) < 2 or len(last_lows) < 2:
            return None

        # Slope calculation
        highs_slope = (last_highs.iloc[-1] - last_highs.iloc[0]) / len(last_highs)
        lows_slope = (last_lows.iloc[-1] - last_lows.iloc[0]) / len(last_lows)

        # Wedge/Pennant: Lines converging
        # Bullish Wedge: Lower Highs (negative slope), Lower Lows (negative slope), but converging?
        # Or Bullish Pennant: Symetric triangle.

        # Let's focus on BREAKOUT logic.
        # If price closes ABOVE the trendline formed by last highs -> Long Breakout

        # Trendline Upper
        x1 = list(last_highs.index)[-2]
        y1 = last_highs.iloc[-2]
        x2 = list(last_highs.index)[-1]
        y2 = last_highs.iloc[-1]

        # Map indices to integer positions for line equation
        # This is tricky with time indices. We'll simplify using index location.
        # But indices in df might be datetime if we set it as index, or ints.
        # data_handler returns RangeIndex usually if we didn't set index.
        # Let's assume RangeIndex for safety or reset it.

        # Simpler approach:
        # If Close > Last Pivot High and Volume is high (checked in main) -> Long
        # If Close < Last Pivot Low -> Short

        current_close = df.iloc[-1]['close']
        last_pivot_high = last_highs.iloc[-1]
        last_pivot_low = last_lows.iloc[-1]

        if current_close > last_pivot_high:
            return "LONG"
        elif current_close < last_pivot_low:
            return "SHORT"

        return None
