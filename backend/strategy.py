
import pandas as pd
import pandas_ta as ta
import numpy as np

class Strategy:
    def __init__(self):
        pass

    def analyze(self, df_5m, df_1h=None):
        """
        Advanced Multi-Timeframe Strategy for Scalping.

        Indicators (5m):
        - EMA 9, EMA 21 (Crossover)
        - VWAP (Trend support)
        - RSI (14) (Momentum/Overbought/Oversold)
        - ADX (14) (Trend Strength)
        - ATR (14) (Volatility)

        Filters:
        - 1H Trend: Price > EMA 20 (1H) for Longs.
        - ADX Filter: ADX > 25 (Avoid chop).
        - RSI Filter: Block Long if > 70, Block Short if < 30.
        """
        if df_5m is None or len(df_5m) < 50:
            return None

        # --- 1. PREPARE 1H TREND FILTER ---
        trend_direction = "NEUTRAL"
        if df_1h is not None and not df_1h.empty and len(df_1h) > 20:
            df_1h['ema_20'] = ta.ema(df_1h['close'], length=20)
            last_1h = df_1h.iloc[-2] # Last closed 1h candle
            if last_1h['close'] > last_1h['ema_20']:
                trend_direction = "UP"
            elif last_1h['close'] < last_1h['ema_20']:
                trend_direction = "DOWN"

        # --- 2. CALCULATE 5M INDICATORS ---
        # EMAs
        df_5m['ema_9'] = ta.ema(df_5m['close'], length=9)
        df_5m['ema_21'] = ta.ema(df_5m['close'], length=21)
        df_5m['ema_200'] = ta.ema(df_5m['close'], length=200)

        # RSI
        df_5m['rsi'] = ta.rsi(df_5m['close'], length=14)

        # ADX
        # adx returns a DF with [ADX_14, DMP_14, DMN_14]
        try:
            adx_df = ta.adx(df_5m['high'], df_5m['low'], df_5m['close'], length=14)
            if adx_df is not None:
                df_5m = pd.concat([df_5m, adx_df], axis=1)
                # Rename default column usually 'ADX_14' -> 'adx'
                if 'ADX_14' in df_5m.columns:
                    df_5m['adx'] = df_5m['ADX_14']
            else:
                df_5m['adx'] = 0
        except:
             df_5m['adx'] = 0

        # ATR (for Risk Management)
        df_5m['atr'] = ta.atr(df_5m['high'], df_5m['low'], df_5m['close'], length=14)

        # VWAP
        if 'vwap' not in df_5m.columns:
            try:
                df_5m.set_index('timestamp', inplace=True, drop=False)
                df_5m['vwap'] = ta.vwap(df_5m['high'], df_5m['low'], df_5m['close'], df_5m['volume'])
                df_5m.reset_index(drop=True, inplace=True)
            except:
                df_5m['vwap'] = df_5m['ema_200'] # Fallback

        # Volume EMA
        df_5m['vol_ema'] = ta.ema(df_5m['volume'], length=20)

        # --- 3. IDENTIFY PIVOTS (Backward Looking) ---
        pivot_highs = []
        pivot_lows = []
        for i in range(len(df_5m) - 3, len(df_5m) - 50, -1):
            if (df_5m['high'].iloc[i] > df_5m['high'].iloc[i-1] and
                df_5m['high'].iloc[i] > df_5m['high'].iloc[i-2] and
                df_5m['high'].iloc[i] > df_5m['high'].iloc[i+1] and
                df_5m['high'].iloc[i] > df_5m['high'].iloc[i+2]):
                pivot_highs.append(df_5m['high'].iloc[i])

            if (df_5m['low'].iloc[i] < df_5m['low'].iloc[i-1] and
                df_5m['low'].iloc[i] < df_5m['low'].iloc[i-2] and
                df_5m['low'].iloc[i] < df_5m['low'].iloc[i+1] and
                df_5m['low'].iloc[i] < df_5m['low'].iloc[i+2]):
                pivot_lows.append(df_5m['low'].iloc[i])

        # Current State
        last_closed_idx = -2
        current_candle = df_5m.iloc[last_closed_idx]
        prev_candle = df_5m.iloc[last_closed_idx - 1]

        signal = None
        setup_type = None
        invalidation_level = None
        atr_value = current_candle['atr'] if pd.notna(current_candle['atr']) else 0
        adx_value = current_candle['adx'] if pd.notna(current_candle['adx']) else 0
        rsi_value = current_candle['rsi'] if pd.notna(current_candle['rsi']) else 50

        # --- LOGIC 1: EMA CROSS with CONFLUENCE ---
        # LONG
        if (prev_candle['ema_9'] <= prev_candle['ema_21'] and current_candle['ema_9'] > current_candle['ema_21']):
            # Filters:
            # 1. 1H Trend must be UP (or neutral if missing)
            # 2. Price > 5m EMA 200 (Local trend)
            # 3. ADX > 20 (Trend Strength)
            # 4. RSI < 70 (Not Overbought)
            if (trend_direction != "DOWN" and
                current_candle['close'] > current_candle['ema_200'] and
                adx_value > 20 and
                rsi_value < 70):

                signal = "LONG"
                setup_type = "MTF_EMA_CROSS"
                invalidation_level = pivot_lows[0] if pivot_lows else current_candle['low'] * 0.995

        # SHORT
        elif (prev_candle['ema_9'] >= prev_candle['ema_21'] and current_candle['ema_9'] < current_candle['ema_21']):
            if (trend_direction != "UP" and
                current_candle['close'] < current_candle['ema_200'] and
                adx_value > 20 and
                rsi_value > 30):

                signal = "SHORT"
                setup_type = "MTF_EMA_CROSS"
                invalidation_level = pivot_highs[0] if pivot_highs else current_candle['high'] * 1.005

        # --- LOGIC 2: BREAKOUT with VOLUME & MOMENTUM ---
        if not signal:
            # Resistance Breakout
            if pivot_highs:
                recent_resistance = pivot_highs[0]
                if prev_candle['close'] <= recent_resistance and current_candle['close'] > recent_resistance:
                    # Filters: Volume + ADX rising + RSI Room + 1H Trend
                    if (current_candle['volume'] > df_5m['vol_ema'].iloc[last_closed_idx] * 1.5 and
                        trend_direction != "DOWN" and
                        rsi_value < 75): # Allow slightly higher RSI for breakouts

                        signal = "LONG"
                        setup_type = "MTF_VOL_BREAKOUT"
                        invalidation_level = current_candle['low']

            # Support Breakdown
            if pivot_lows:
                recent_support = pivot_lows[0]
                if prev_candle['close'] >= recent_support and current_candle['close'] < recent_support:
                     if (current_candle['volume'] > df_5m['vol_ema'].iloc[last_closed_idx] * 1.5 and
                        trend_direction != "UP" and
                        rsi_value > 25):

                        signal = "SHORT"
                        setup_type = "MTF_VOL_BREAKOUT"
                        invalidation_level = current_candle['high']

        if signal:
            return {
                "signal": signal,
                "type": setup_type,
                "entry_price": current_candle['close'],
                "timestamp": current_candle['timestamp'],
                "invalidation_level": invalidation_level,
                "atr": atr_value
            }

        return None
