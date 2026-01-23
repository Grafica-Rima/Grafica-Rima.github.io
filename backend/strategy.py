
import pandas as pd
import pandas_ta as ta
import numpy as np

class Strategy:
    def __init__(self):
        pass

    def analyze(self, df):
        """
        Refactored analysis logic for 5m scalping.
        Removes look-ahead bias, uses faster EMAs (9/21), VWAP, and Trend Filter.
        """
        if df is None or len(df) < 50:
            return None

        # 1. Calculate Indicators
        # Scalping EMAs
        df['ema_9'] = ta.ema(df['close'], length=9)
        df['ema_21'] = ta.ema(df['close'], length=21)

        # Trend Filter (Higher timeframe bias approximation)
        df['ema_200'] = ta.ema(df['close'], length=200)

        # VWAP (Volume Weighted Average Price)
        # Standard VWAP usually anchors to session start, but pandas_ta default handles dataframe.
        # For continuous futures, a rolling VWAP or standard calculation is acceptable.
        if 'vwap' not in df.columns:
            try:
                # pandas_ta vwap might return None if indices are not datetime
                df.set_index('timestamp', inplace=True, drop=False)
                df['vwap'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
                df.reset_index(drop=True, inplace=True)
            except Exception as e:
                print(f"VWAP Error: {e}")
                df['vwap'] = df['ema_200'] # Fallback

        # Volume EMA
        df['vol_ema'] = ta.ema(df['volume'], length=20)

        # 2. Identify Pivots (No Look-ahead)
        # A pivot high at index 'i' is valid if high[i] > high[i-1] and high[i] > high[i-2] ...
        # AND we confirm it after 'n' bars.
        # However, for support/resistance levels to trade AGAINST, we use past pivots.
        # We define a pivot high as a candle that was higher than 2 candles before and 2 candles after.
        # This means a pivot at 'i' is known at 'i+2'.

        window = 3
        # Create shifting for vectorization to find peaks in the PAST
        # We need to know if row[i-3] was a peak.
        # It was a peak if high[i-3] > high[i-4], high[i-5]... and high[i-3] > high[i-2], high[i-1]

        # Simpler approach: Rolling Max over window.
        # If High[i-window] == RollingMax(window*2+1) centered at i-window...
        # But we are at 'current_candle'. We just look back.

        # Let's iterate backwards to find the most recent valid pivots for Support/Resistance
        # A pivot is confirmed if 2 subsequent candles close lower (for high).
        pivot_highs = [] # list of (index, price)
        pivot_lows = []

        # We scan the last 50 candles for pivots.
        # We stop at -3 because we need 2 bars to confirm.
        for i in range(len(df) - 3, len(df) - 50, -1):
            # Check for High Pivot at i
            # Condition: High[i] > High[i-1] and High[i] > High[i-2]
            # AND High[i] > High[i+1] and High[i] > High[i+2]
            if (df['high'].iloc[i] > df['high'].iloc[i-1] and
                df['high'].iloc[i] > df['high'].iloc[i-2] and
                df['high'].iloc[i] > df['high'].iloc[i+1] and
                df['high'].iloc[i] > df['high'].iloc[i+2]):
                pivot_highs.append(df['high'].iloc[i])

            # Check for Low Pivot
            if (df['low'].iloc[i] < df['low'].iloc[i-1] and
                df['low'].iloc[i] < df['low'].iloc[i-2] and
                df['low'].iloc[i] < df['low'].iloc[i+1] and
                df['low'].iloc[i] < df['low'].iloc[i+2]):
                pivot_lows.append(df['low'].iloc[i])

        # Current State
        last_closed_idx = -2 # The last fully completed candle
        current_candle = df.iloc[last_closed_idx]
        prev_candle = df.iloc[last_closed_idx - 1]

        # 3. Strategy Logic
        # We look for confluence.

        signal = None
        setup_type = None
        invalidation_level = None

        # --- LOGIC 1: EMA CROSS with TREND FILTER ---
        # Long: EMA 9 crosses above EMA 21 AND Price > EMA 200 AND Price > VWAP
        if (prev_candle['ema_9'] <= prev_candle['ema_21'] and current_candle['ema_9'] > current_candle['ema_21']):
            # Bullish Cross
            if current_candle['close'] > current_candle['ema_200']: # Trend Filter
                 signal = "LONG"
                 setup_type = "EMA_CROSS_TREND"
                 # SL below the recent swing low or EMA 21
                 invalidation_level = pivot_lows[0] if pivot_lows else current_candle['low'] * 0.995

        elif (prev_candle['ema_9'] >= prev_candle['ema_21'] and current_candle['ema_9'] < current_candle['ema_21']):
            # Bearish Cross
            if current_candle['close'] < current_candle['ema_200']: # Trend Filter
                signal = "SHORT"
                setup_type = "EMA_CROSS_TREND"
                invalidation_level = pivot_highs[0] if pivot_highs else current_candle['high'] * 1.005

        # --- LOGIC 2: BREAKOUT with VOLUME ---
        # If we didn't get an EMA signal, check for Breakout
        if not signal:
            # Resistance Breakout
            if pivot_highs:
                recent_resistance = pivot_highs[0]
                # Check if we just broke it
                if prev_candle['close'] <= recent_resistance and current_candle['close'] > recent_resistance:
                    # Filter: Volume Spike
                    if current_candle['volume'] > df['vol_ema'].iloc[last_closed_idx] * 1.5:
                        signal = "LONG"
                        setup_type = "VOL_BREAKOUT"
                        invalidation_level = current_candle['low'] # Low of breakout candle is strict SL

            # Support Breakdown
            if pivot_lows:
                recent_support = pivot_lows[0]
                if prev_candle['close'] >= recent_support and current_candle['close'] < recent_support:
                    if current_candle['volume'] > df['vol_ema'].iloc[last_closed_idx] * 1.5:
                        signal = "SHORT"
                        setup_type = "VOL_BREAKOUT"
                        invalidation_level = current_candle['high']

        # --- LOGIC 3: VWAP BOUNCE (Micro Scalp) ---
        # Price touches VWAP and bounces
        if not signal:
            vwap = current_candle['vwap']
            if pd.notna(vwap):
                dist_pct = abs(current_candle['close'] - vwap) / vwap
                # Near VWAP (0.2%)
                if dist_pct < 0.002:
                     # Check candle shape (Hammer / Rejection) logic could go here
                     # For now, simple Trend check
                     pass

        if signal:
            return {
                "signal": signal,
                "type": setup_type,
                "entry_price": current_candle['close'],
                "timestamp": current_candle['timestamp'],
                "invalidation_level": invalidation_level
            }

        return None
