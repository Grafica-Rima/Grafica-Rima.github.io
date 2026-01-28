import pandas as pd
import pandas_ta as ta
import numpy as np
from config import Config

class Strategy:
    def __init__(self):
        self.ema_fast = Config.EMA_FAST
        self.ema_slow = Config.EMA_SLOW
        self.ema_trend = Config.EMA_TREND

    def analyze(self, df):
        """
        Analyzes the DataFrame and returns a signal.
        Logic is strictly based on the LAST CLOSED CANDLE (df.iloc[-2]) and history.
        """
        if len(df) < self.ema_trend + 50:
            return "NEUTRAL"

        # 1. Indicators Calculation
        df['EMA_FAST'] = ta.ema(df['close'], length=self.ema_fast)
        df['EMA_SLOW'] = ta.ema(df['close'], length=self.ema_slow)
        df['EMA_TREND'] = ta.ema(df['close'], length=self.ema_trend)
        df['VOL_MA'] = ta.sma(df['volume'], length=20)

        # Anti-Chop Filters
        # ADX > 25 indicates trend presence
        # ADX is already added by data_handler if supported, otherwise calc here
        if 'ADX' not in df.columns:
             adx = ta.adx(df['high'], df['low'], df['close'], length=14)
             if adx is not None: df['ADX'] = adx['ADX_14']

        # Candle Selection: strictly closed candles
        # current = iloc[-1] (Open), last_closed = iloc[-2]
        # logic must rely on closed data for entry confirmation
        last_closed = df.iloc[-2]
        prev_closed = df.iloc[-3]

        signal = "NEUTRAL"

        # 2. Chop & Trend Filters
        # ADX Check
        adx_val = last_closed.get('ADX', 0)
        is_trending = adx_val > 25

        # EMA Distance Check (avoid tight EMAs)
        ema_dist = abs(last_closed['EMA_FAST'] - last_closed['EMA_SLOW'])
        min_dist_threshold = last_closed['close'] * 0.0005 # 0.05% distance
        is_separated = ema_dist > min_dist_threshold

        if not (is_trending and is_separated):
            return "NEUTRAL"

        # 3. Setup Detection
        trend_bullish = last_closed['close'] > last_closed['EMA_TREND']
        trend_bearish = last_closed['close'] < last_closed['EMA_TREND']

        # 4. Trigger Events (on Closed Candle)

        # A. EMA Cross
        ma_cross_up = (prev_closed['EMA_FAST'] <= prev_closed['EMA_SLOW']) and (last_closed['EMA_FAST'] > last_closed['EMA_SLOW'])
        ma_cross_down = (prev_closed['EMA_FAST'] >= prev_closed['EMA_SLOW']) and (last_closed['EMA_FAST'] < last_closed['EMA_SLOW'])

        # B. Pattern Breakout (Local Pivots without lookahead)
        pattern_signal = self._detect_pattern_breakout_safe(df)

        # C. Fibonacci Support/Resistance (Using past swings)
        is_fib_support = self._check_fibonacci_safe(df, 'support')
        is_fib_resistance = self._check_fibonacci_safe(df, 'resistance')

        # 5. Volume Confirmation
        vol_increasing = last_closed['volume'] > last_closed['VOL_MA']

        # 6. Signal Combination
        if trend_bullish:
            triggers = [ma_cross_up, pattern_signal == "LONG", is_fib_support]
            if any(triggers) and vol_increasing:
                signal = "LONG"

        elif trend_bearish:
            triggers = [ma_cross_down, pattern_signal == "SHORT", is_fib_resistance]
            if any(triggers) and vol_increasing:
                signal = "SHORT"

        return signal

    def _get_past_pivots(self, df, window=5):
        """
        Finds pivots strictly in the PAST.
        A pivot high at index `i` is confirmed if `i` was higher than neighbors
        at `i-window`...`i-1` and `i+1`...`i+window` (BUT we must be currently at `i+window+1` or later).
        """
        # We only look at data up to iloc[-2] (last closed)
        # To find a pivot confirmed 5 bars ago, we look at slice [:-1]

        # Simple approach: Find local max/min in rolling window, check if center is extrema
        # We need specific distinct peaks.

        # Optimization: Just look at the last 50 closed candles
        subset = df.iloc[-60:-1].copy() # Exclude developing candle

        # Check if a candle was a local high/low relative to neighbors
        # We iterate backwards from current closed
        highs = []
        lows = []

        for i in range(len(subset) - window - 1, window, -1):
            center = subset.iloc[i]
            left = subset.iloc[i-window:i]
            right = subset.iloc[i+1:i+window+1]

            if center['high'] >= left['high'].max() and center['high'] >= right['high'].max():
                highs.append(center['high'])

            if center['low'] <= left['low'].min() and center['low'] <= right['low'].min():
                lows.append(center['low'])

            if len(highs) >= 2 and len(lows) >= 2:
                break

        return highs, lows

    def _check_fibonacci_safe(self, df, mode):
        # Use Swing High/Low from the *previous* market structure (e.g., last 100 closed candles)
        # Exclude recent 5 to avoid testing against current forming swing
        subset = df.iloc[-100:-5]
        max_price = subset['high'].max()
        min_price = subset['low'].min()

        diff = max_price - min_price
        if diff == 0: return False

        # Fib 0.618 retracement level
        # Bullish Retracement: Price dropped to min + 0.618 * range?
        # Usually Retracement is measured from Swing Low to Swing High.
        # 0.618 Retracement level = Swing High - 0.618 * (High - Low)
        fib_618_level = max_price - (0.618 * diff)

        # Current closed price
        current_price = df.iloc[-2]['close']
        tolerance = current_price * 0.001 # 0.1% tolerance

        if mode == 'support':
            # Price bouncing UP from 0.618 level?
            # Or just sitting near it.
            if abs(current_price - fib_618_level) < tolerance:
                return True

        # For resistance (Bearish Retracement):
        # Price rose to Swing Low + 0.618 * range?
        fib_618_bearish = min_price + (0.618 * diff)
        if mode == 'resistance':
             if abs(current_price - fib_618_bearish) < tolerance:
                return True

        return False

    def _detect_pattern_breakout_safe(self, df):
        """
        Detects breakout of recent pivots (Support/Resistance Flip).
        """
        highs, lows = self._get_past_pivots(df, window=3)

        if not highs or not lows: return None

        last_pivot_high = highs[0] # Most recent pivot high
        last_pivot_low = lows[0]   # Most recent pivot low

        current_close = df.iloc[-2]['close']
        prev_close = df.iloc[-3]['close']

        # Breakout Long: Close crossed above last pivot high
        if prev_close < last_pivot_high and current_close > last_pivot_high:
            return "LONG"

        # Breakout Short: Close crossed below last pivot low
        if prev_close > last_pivot_low and current_close < last_pivot_low:
            return "SHORT"

        return None
