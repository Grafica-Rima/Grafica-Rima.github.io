
import pandas as pd
import pandas_ta as ta
import numpy as np

class Strategy:
    def __init__(self):
        self.last_signal = None

    def analyze(self, df):
        """
        Analyzes the dataframe to find patterns, Elliott waves, Fib levels, and volume/MA signals.
        Returns a dict with signal information or None.
        """
        if df is None or len(df) < 50:
            return None

        # Add indicators
        # EMAs
        df['ema_50'] = ta.ema(df['close'], length=50)
        df['ema_200'] = ta.ema(df['close'], length=200)

        # Volume EMA for accumulation analysis
        df['vol_ema'] = ta.ema(df['volume'], length=20)

        # Last closed candle (since we are on 5m, we look at the last fully closed row)
        # The dataframe usually has the last row as the currently open candle if fetched "now".
        # We need the previous row [-2] as the "last closed candle".
        last_closed_idx = -2
        current_candle = df.iloc[last_closed_idx]
        prev_candle = df.iloc[last_closed_idx - 1]

        # 1. Pattern Recognition (Simplified Wedges/Pennants via Local Extrema)
        # We look for lower highs and higher lows (Triangle/Pennant)
        # Or Lower highs + Lower lows (Channel/Wedge)
        # This is a complex topic, simplified here for robustness.

        # Find swings (pivot points) in the last 50 periods
        # We use a simple window method
        window = 5
        df['is_pivot_high'] = df['high'].rolling(window=window*2+1, center=True).apply(lambda x: x[window] == max(x), raw=True)
        df['is_pivot_low'] = df['low'].rolling(window=window*2+1, center=True).apply(lambda x: x[window] == min(x), raw=True)

        pivot_highs = df[df['is_pivot_high'] == 1].copy()
        pivot_lows = df[df['is_pivot_low'] == 1].copy()

        # Check for breakouts in the last candle
        signal = None
        signal_type = None
        entry_price = current_candle['close']

        # 2. Fibonacci & Elliott Wave (Simplified)
        # Identify the last major impulse
        # If we have a significant recent low and high, calculate fibs
        if len(pivot_lows) > 0 and len(pivot_highs) > 0:
            last_low = pivot_lows.iloc[-1]['low']
            last_high = pivot_highs.iloc[-1]['high']

            diff = last_high - last_low
            fib_618 = last_high - (diff * 0.618)
            fib_1618_ext = last_high + (diff * 0.618) # Simplified extension

            # Check for bounce off 0.618 (Bullish Retracement)
            # If price dipped near 0.618 and closed above it with volume
            if (prev_candle['low'] <= fib_618 * 1.001 and current_candle['close'] > fib_618):
                 # Confirm with Volume Increase
                if current_candle['volume'] > df['vol_ema'].iloc[last_closed_idx]:
                    signal = "LONG"
                    signal_type = "FIB_618_BOUNCE"

        # 3. Moving Average Cross (Golden Cross / Death Cross)
        # Check crossover in the last closed candle
        if (prev_candle['ema_50'] < prev_candle['ema_200']) and (current_candle['ema_50'] > current_candle['ema_200']):
            signal = "LONG"
            signal_type = "EMA_CROSS"
        elif (prev_candle['ema_50'] > prev_candle['ema_200']) and (current_candle['ema_50'] < current_candle['ema_200']):
            signal = "SHORT"
            signal_type = "EMA_CROSS"

        # 4. Breakout logic (Resistance/Support)
        # If closing price breaks the last swing high/low with volume
        if len(pivot_highs) > 1:
            last_swing_high = pivot_highs.iloc[-1]['high']
            if prev_candle['close'] <= last_swing_high and current_candle['close'] > last_swing_high:
                 if current_candle['volume'] > df['vol_ema'].iloc[last_closed_idx] * 1.2: # Strong volume
                    signal = "LONG"
                    signal_type = "BREAKOUT_RESISTANCE"

        if len(pivot_lows) > 1:
            last_swing_low = pivot_lows.iloc[-1]['low']
            if prev_candle['close'] >= last_swing_low and current_candle['close'] < last_swing_low:
                 if current_candle['volume'] > df['vol_ema'].iloc[last_closed_idx] * 1.2:
                    signal = "SHORT"
                    signal_type = "BREAKOUT_SUPPORT"

        if signal:
            return {
                "signal": signal,
                "type": signal_type,
                "entry_price": entry_price,
                "timestamp": current_candle['timestamp'],
                "support_level": pivot_lows.iloc[-1]['low'] if len(pivot_lows) > 0 else entry_price * 0.99,
                "resistance_level": pivot_highs.iloc[-1]['high'] if len(pivot_highs) > 0 else entry_price * 1.01
            }

        return None
