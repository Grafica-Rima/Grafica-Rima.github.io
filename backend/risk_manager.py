from config import Config

class RiskManager:
    def __init__(self):
        self.rr_ratio = Config.RISK_REWARD_RATIO
        self.sl_multiplier = 1.2 # Multiplier for ATR (Optimized for 5m Scalping/Strong Trend)

    def calculate_entry_params(self, signal_type, current_price, df, atr=0):
        """
        Calculates fixed Entry, Stop Loss, and Take Profit using ATR and Structure.

        atr: The ATR value of the last closed candle.
        """
        stop_loss = 0.0
        take_profit = 0.0
        entry_price = current_price

        # Fallback if ATR is missing/zero
        if not atr or atr == 0:
            atr = current_price * 0.01 # 1% fallback

        # Lookback for Structure (last 10 closed candles)
        lookback = 10
        subset = df.iloc[-lookback-1:-1] # Exclude current open

        recent_low = subset['low'].min()
        recent_high = subset['high'].max()

        if signal_type == "LONG":
            # SL = Structure Low - (1.5 * ATR)
            # This avoids "liquidity grabs" exactly at the wick
            stop_loss = recent_low - (self.sl_multiplier * atr)

            # Safety: Ensure SL is below Entry
            if stop_loss >= entry_price:
                 stop_loss = entry_price - (2 * atr)

            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * self.rr_ratio)

        elif signal_type == "SHORT":
            # SL = Structure High + (1.5 * ATR)
            stop_loss = recent_high + (self.sl_multiplier * atr)

            # Safety: Ensure SL is above Entry
            if stop_loss <= entry_price:
                stop_loss = entry_price + (2 * atr)

            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * self.rr_ratio)

        return {
            "entry": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }
