
class RiskManager:
    def __init__(self):
        pass

    def calculate_trade_params(self, signal_data):
        """
        Calculates fixed Entry, Stop Loss, and Take Profit.

        Strategy:
        - LONG:
          - SL: Slightly below recent support or low of the signal candle.
          - TP: 1.5x to 2x distance to SL (Risk:Reward ratio).
        - SHORT:
          - SL: Slightly above recent resistance or high of the signal candle.
          - TP: 1.5x to 2x distance to SL.
        """
        signal = signal_data['signal']
        entry = signal_data['entry_price']

        # Risk Management Settings
        risk_reward_ratio = 2.0

        if signal == "LONG":
            # If we have a support level from the strategy, use it. Otherwise use 1% default.
            support = signal_data.get('support_level', entry * 0.99)

            # Ensure SL is not too close (min 0.2%)
            if (entry - support) / entry < 0.002:
                support = entry * 0.995

            stop_loss = support
            risk = entry - stop_loss
            take_profit = entry + (risk * risk_reward_ratio)

        elif signal == "SHORT":
            resistance = signal_data.get('resistance_level', entry * 1.01)

            if (resistance - entry) / entry < 0.002:
                resistance = entry * 1.005

            stop_loss = resistance
            risk = stop_loss - entry
            take_profit = entry - (risk * risk_reward_ratio)

        else:
            return None

        return {
            "entry": float(entry),
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "side": signal
        }
