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
        PRO SETUP: Trend (EMA200) + ADX > 20 + Pivot Breakout + Volume.
        """
        if len(df) < self.ema_trend + 50:
            return "NEUTRAL"

        # 1. Indicators Calculation
        df['EMA_FAST'] = ta.ema(df['close'], length=self.ema_fast)
        df['EMA_SLOW'] = ta.ema(df['close'], length=self.ema_slow)
        df['EMA_TREND'] = ta.ema(df['close'], length=self.ema_trend)
        df['VOL_MA'] = ta.sma(df['volume'], length=20)

        # Calculate ADX if missing
        if 'ADX' not in df.columns:
             adx = ta.adx(df['high'], df['low'], df['close'], length=14)
             if adx is not None: df['ADX'] = adx['ADX_14']

        # Candle Selection: strictly closed candles
        last_closed = df.iloc[-2]

        signal = "NEUTRAL"

        # 2. Chop & Trend Filters
        # ADX Check (Using new threshold 20)
        adx_val = last_closed.get('ADX', 0)
        is_trending = adx_val > Config.ADX_THRESHOLD

        if not is_trending:
            return "NEUTRAL"

        # 3. Setup Detection (Single Setup: Trend Follow)
        trend_bullish = last_closed['close'] > last_closed['EMA_TREND']
        trend_bearish = last_closed['close'] < last_closed['EMA_TREND']

        # 4. Trigger Events (on Closed Candle)

        # Strict Pattern Breakout ONLY
        pattern_signal = self._detect_pattern_breakout_safe(df)

        # 5. Volume Confirmation
        vol_increasing = last_closed['volume'] > last_closed['VOL_MA']

        # 6. Signal Combination
        if trend_bullish and pattern_signal == "LONG" and vol_increasing:
            signal = "LONG"

        elif trend_bearish and pattern_signal == "SHORT" and vol_increasing:
            signal = "SHORT"

        return signal

    def _get_past_pivots(self, df, window=5):
        """
        Finds pivots strictly in the PAST.
        """
        subset = df.iloc[-60:-1].copy() # Exclude developing candle

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
