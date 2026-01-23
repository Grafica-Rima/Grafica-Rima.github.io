
class RiskManager:
    def __init__(self):
        pass

    def calculate_trade_params(self, signal_data):
        """
        Calculates fixed Entry, Stop Loss, and Take Profit.
        Uses strict Risk:Reward.
        """
        signal = signal_data['signal']
        entry = float(signal_data['entry_price'])
        invalidation = float(signal_data.get('invalidation_level', 0.0))

        # Default Risk Settings
        min_risk_reward = 2.0
        min_stop_distance_pct = 0.002 # 0.2% minimum stop width to avoid noise

        if signal == "LONG":
            stop_loss = invalidation

            # Sanity Check: If SL is above entry (impossible for LONG) or too close
            if stop_loss >= entry or (entry - stop_loss) / entry < min_stop_distance_pct:
                stop_loss = entry * (1 - min_stop_distance_pct)

            risk = entry - stop_loss
            take_profit = entry + (risk * min_risk_reward)

        elif signal == "SHORT":
            stop_loss = invalidation

            # Sanity Check
            if stop_loss <= entry or (stop_loss - entry) / entry < min_stop_distance_pct:
                stop_loss = entry * (1 + min_stop_distance_pct)

            risk = stop_loss - entry
            take_profit = entry - (risk * min_risk_reward)

        else:
            return None

        return {
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "side": signal,
            "setup_type": signal_data.get('type', 'Unknown')
        }
