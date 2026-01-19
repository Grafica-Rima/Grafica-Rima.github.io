import pandas as pd
import pandas_ta as ta
import numpy as np

class Strategy:
    def __init__(self):
        pass

    def analyze(self, df):
        """
        Analyzes the DataFrame (OHLCV) and returns a signal if any.
        Returns:
            signal (str): "LONG", "SHORT", or None
            details (dict): Info about why the signal was triggered
        """
        if df is None or len(df) < 50:
            return None, {}

        # 1. Indicators Calculation
        df['rsi'] = df.ta.rsi(length=14)
        df['ema_50'] = df.ta.ema(length=50)
        df['ema_200'] = df.ta.ema(length=200)

        # Volume Moving Average
        df['vol_ma'] = df['volume'].rolling(window=20).mean()

        # Last closed candle (row -1 is current open candle usually in real-time streams,
        # but here depends on data source. Assuming -1 is the last CLOSED candle for safety)
        # Wait, usually fetching OHLCV includes the open candle at the end.
        # User said: "Cuando abre una vela nueva el programa debe darle prioridad a la última vela cerrada"
        # So we look at -2 if -1 is the currently open candle.
        # However, typical CCXT fetch might return the last completed one or include the current one.
        # Let's assume the last row is the CURRENT OPEN candle, so we analyze the one before it (-2).

        current_candle = df.iloc[-1]
        last_closed_candle = df.iloc[-2]
        prev_closed_candle = df.iloc[-3]

        # 2. Pattern Recognition (Basic approach for Wedges/Flags via High/Low slopes)
        # We need to look back a bit.
        lookback = 20
        recent_df = df.iloc[-lookback-2:-2] # Exclude current open and just closed

        # Find local peaks and troughs
        # This is a simplification. Real pattern matching is complex.
        # We will focus on the breakout logic and Volume.

        signal = None
        reason = []

        # --- Logic Checks ---

        # A. Volume Confirmation
        # Check if volume is increasing on the breakout candle (last closed)
        volume_increasing = last_closed_candle['volume'] > last_closed_candle['vol_ma']

        # B. Moving Average Crossover / Support / Resistance
        # Golden Cross (Fast crosses above Slow) logic or Price crossing MA
        price_above_ema50 = last_closed_candle['close'] > last_closed_candle['ema_50']
        price_above_ema200 = last_closed_candle['close'] > last_closed_candle['ema_200']

        # C. Fibonacci Retracement / Extension Logic (Simplified)
        # We need a defined swing to calculate Fibs.
        # Let's define the recent high and low over 50 periods.
        recent_high = df['high'].iloc[-50:-2].max()
        recent_low = df['low'].iloc[-50:-2].min()
        diff = recent_high - recent_low

        fib_0618_level = recent_low + (diff * 0.618)
        fib_1618_extension_up = recent_high + (diff * 0.618) # Simplified extension

        # Check for bounce off 0.618 (Pullback Strategy)
        # If price dipped to 0.618 and closed above it.
        near_fib_0618 = abs(last_closed_candle['low'] - fib_0618_level) / fib_0618_level < 0.002 # Within 0.2%

        # D. Breakout Logic (Resistance/Support)
        # If price breaks recent high with volume
        breakout_up = (last_closed_candle['close'] > recent_high) and volume_increasing
        breakout_down = (last_closed_candle['close'] < recent_low) and volume_increasing

        # --- SIGNAL GENERATION ---

        # LONG Signal Conditions
        if breakout_up:
            signal = "LONG"
            reason.append("Breakout of recent high with volume")
        elif (prev_closed_candle['close'] < fib_0618_level) and (last_closed_candle['close'] > fib_0618_level) and volume_increasing:
             # Reclaiming Fib 0.618
            signal = "LONG"
            reason.append("Bounce off Fib 0.618 with volume")
        elif (prev_closed_candle['close'] < last_closed_candle['ema_50']) and (last_closed_candle['close'] > last_closed_candle['ema_50']) and volume_increasing:
             # MA Breakout
             signal = "LONG"
             reason.append("EMA 50 Breakout")

        # SHORT Signal Conditions
        elif breakout_down:
            signal = "SHORT"
            reason.append("Breakdown of recent low with volume")
        elif (prev_closed_candle['close'] > last_closed_candle['ema_50']) and (last_closed_candle['close'] < last_closed_candle['ema_50']) and volume_increasing:
            signal = "SHORT"
            reason.append("EMA 50 Breakdown")


        # Collect Support/Resistance levels for Risk Manager
        # We use simple pivots or the High/Low we found
        sr_levels = [recent_low, recent_high, last_closed_candle['ema_50'], last_closed_candle['ema_200'], fib_0618_level]
        fib_levels = [fib_0618_level, fib_1618_extension_up]

        return signal, {
            "reason": ", ".join(reason),
            "sr_levels": sr_levels,
            "fib_levels": fib_levels,
            "close_price": last_closed_candle['close']
        }
