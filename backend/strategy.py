
import pandas as pd
import pandas_ta as ta
import numpy as np

class Strategy:
    def __init__(self):
        pass

    def analyze(self, df):
        """
        Main analysis function.
        df: DataFrame with open, high, low, close, volume.
        Returns: Dict with indicators and potential signal.
        """
        if df.empty or len(df) < 50:
            return None

        # 1. Calculate Indicators
        # Moving Averages
        df['EMA_50'] = ta.ema(df['close'], length=50)
        df['EMA_200'] = ta.ema(df['close'], length=200)

        # RSI
        df['RSI'] = ta.rsi(df['close'], length=14)

        # ATR for Risk Management
        df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)

        # Volume Moving Average
        df['VOL_MA'] = ta.sma(df['volume'], length=20)

        # Fibonacci Retracement Levels (based on recent significant High/Low in last 50 candles)
        # We find the max high and min low of the recent window to estimate current range
        recent_window = 50
        recent_high = df['high'].rolling(window=recent_window).max()
        recent_low = df['low'].rolling(window=recent_window).min()

        # 2. Pattern Recognition (Heuristic)
        # We look at the last completed candle (row -1) and the one before (-2)
        last_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]

        signal = None
        reason = []

        # --- LOGIC ---

        # A. Volume Check
        # Is volume increasing?
        volume_spike = last_candle['volume'] > last_candle['VOL_MA'] * 1.5
        if volume_spike:
            reason.append("High Volume detected")

        # B. Moving Average Cross (Golden/Death Cross check on lower timeframe context)
        # or just Price vs EMA
        trend_bullish = last_candle['close'] > last_candle['EMA_50']
        trend_bearish = last_candle['close'] < last_candle['EMA_50']

        # C. Fibonacci check
        # We calculate Fib levels of the *previous* major move.
        # This is hard to perfect automatically, so we use the recent range.
        diff = recent_high.iloc[-1] - recent_low.iloc[-1]
        fib_618_level_bull = recent_low.iloc[-1] + (diff * 0.618)
        fib_382_level_bull = recent_low.iloc[-1] + (diff * 0.382)

        # D. Pattern: Wedge/Flag (Simplified)
        # We look for lower volatility (consolidation) followed by a breakout.
        # Measure candle body size average
        avg_body = (df['close'] - df['open']).abs().rolling(10).mean()
        is_consolidating = (abs(prev_candle['close'] - prev_candle['open']) < avg_body.iloc[-2] * 0.8)

        # E. Entry Signal Logic

        # LONG SIGNAL
        # 1. Price is above EMA 50 (Trend is up)
        # 2. Price retraced to Fib 0.618 or 0.5 recently and is now bouncing?
        #    OR Breakout from consolidation with Volume.

        if trend_bullish:
            # Scenario 1: Breakout
            if is_consolidating and volume_spike and last_candle['close'] > prev_candle['high']:
                 signal = 'LONG'
                 reason.append("Bullish Flag/Wedge Breakout with Volume")

            # Scenario 2: Fib Retracement Bounce
            # Price touched near 0.618 of recent range and closed above it (assuming recent range was an impulse)
            # This assumes the 'recent_low' to 'recent_high' was the move. If price dropped, it's a retracement.
            # (Simplification for automation)
            elif (last_candle['low'] <= fib_618_level_bull) and (last_candle['close'] > fib_618_level_bull):
                 # Check RSI not overbought
                 if last_candle['RSI'] < 70:
                     signal = 'LONG'
                     reason.append("Bounce off 0.618 Fib Support")

        # SHORT SIGNAL
        elif trend_bearish:
            # Scenario 1: Bearish Breakout
            if is_consolidating and volume_spike and last_candle['close'] < prev_candle['low']:
                signal = 'SHORT'
                reason.append("Bearish Flag/Wedge Breakdown with Volume")

            # Scenario 2: Fib Retracement Rejection (Inverse logic for shorts roughly applied)
            # Just simple resistance check for now
            elif last_candle['RSI'] > 70: # Overbought divergence potential
                 pass # Complex to code divergence without more state, keeping it simple.

        return {
            'signal': signal,
            'reason': ", ".join(reason) if reason else None,
            'close': last_candle['close'],
            'atr': last_candle['ATR'],
            'support': recent_low.iloc[-1], # approximate
            'resistance': recent_high.iloc[-1] # approximate
        }
