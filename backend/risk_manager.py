
class RiskManager:
    def __init__(self, atr_multiplier_sl=1.5, risk_reward_ratio=2.0):
        self.atr_multiplier_sl = atr_multiplier_sl
        self.risk_reward_ratio = risk_reward_ratio

    def calculate_tp_sl(self, signal_type, entry_price, atr_value, support=None, resistance=None):
        """
        Calculates fixed TP and SL based on ATR and/or Support/Resistance structures.
        """
        stop_loss = 0.0
        take_profit = 0.0

        # Base SL on ATR volatility
        sl_distance = atr_value * self.atr_multiplier_sl

        if signal_type == 'LONG':
            # If there is a strong support nearby, use it, otherwise use ATR
            if support and support < entry_price:
                 # Ensure support isn't too far (risk management)
                 if (entry_price - support) < (sl_distance * 1.5):
                     stop_loss = support
                 else:
                     stop_loss = entry_price - sl_distance
            else:
                stop_loss = entry_price - sl_distance

            risk = entry_price - stop_loss
            take_profit = entry_price + (risk * self.risk_reward_ratio)

            # If resistance is nearby and lower than calculated TP, we might adjust or invalidate (simplified here)
            # but user wants FIXED TP/SL once detected.

        elif signal_type == 'SHORT':
            if resistance and resistance > entry_price:
                if (resistance - entry_price) < (sl_distance * 1.5):
                    stop_loss = resistance
                else:
                    stop_loss = entry_price + sl_distance
            else:
                stop_loss = entry_price + sl_distance

            risk = stop_loss - entry_price
            take_profit = entry_price - (risk * self.risk_reward_ratio)

        return round(take_profit, 2), round(stop_loss, 2)
