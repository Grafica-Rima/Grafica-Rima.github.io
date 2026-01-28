from config import Config

class RiskManager:
    def __init__(self):
        self.rr_ratio = Config.RISK_REWARD_RATIO

    def calculate_entry_params(self, signal_type, current_price, df):
        """
        Calculates fixed Entry, Stop Loss, and Take Profit.

        df: DataFrame containing OHLCV data to find swing points for SL.
        """
        stop_loss = 0.0
        take_profit = 0.0
        entry_price = current_price

        # Basic Swing Detection for SL (Look back 10 candles)
        # In a real professional app, this would use more sophisticated pivot detection
        lookback = 10
        recent_low = df['low'].iloc[-lookback:].min()
        recent_high = df['high'].iloc[-lookback:].max()

        if signal_type == "LONG":
            # SL is recent low. If recent low is too close, use a default buffer (e.g. 0.5%)
            stop_loss = recent_low

            # Safety check: if SL >= Entry (impossible for Long), force a buffer
            if stop_loss >= entry_price:
                stop_loss = entry_price * 0.995

            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * self.rr_ratio)

        elif signal_type == "SHORT":
            # SL is recent high
            stop_loss = recent_high

            # Safety check
            if stop_loss <= entry_price:
                stop_loss = entry_price * 1.005

            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * self.rr_ratio)

        return {
            "entry": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit
        }
