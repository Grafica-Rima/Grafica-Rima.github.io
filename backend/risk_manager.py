
class RiskManager:
    def __init__(self):
        pass

    def calculate_trade_params(self, signal_data):
        """
        Calculates fixed Entry, Stop Loss, and Take Profit.
        Uses ATR to buffer the Stop Loss and enforces 1:2 R:R.
        """
        signal = signal_data['signal']
        entry = float(signal_data['entry_price'])
        invalidation = float(signal_data.get('invalidation_level', 0.0))
        atr = float(signal_data.get('atr', 0.0))

        # Risk Settings
        risk_reward_ratio = 2.0
        min_stop_distance_pct = 0.002 # 0.2% absolute minimum
        atr_multiplier = 1.5 # Buffer multiplier

        # Sanity check for ATR
        if atr <= 0:
            atr = entry * 0.005 # Fallback if ATR missing

        buffer = atr * atr_multiplier

        if signal == "LONG":
            # Initial SL based on pivot
            technical_sl = invalidation

            # ATR Adjusted SL: Ensure SL is at least 'buffer' away from entry
            # If technical SL is too close (noise), move it down.
            # If technical SL is too far, we might want to cap it?
            # (Usually we respect the pivot, but for profitability we avoid huge stops).
            # Let's strictly use the wider of (Pivot) OR (Entry - Buffer) to be safe from noise.

            volatility_sl = entry - buffer

            # We take the lower one (wider stop) to avoid being wicked out,
            # UNLESS the pivot is waaaay too far.
            # But "profitable as possible" usually means tight stops.
            # Let's stick to: Use Pivot, but if Pivot is too close (< 1 ATR), widen to 1.5 ATR.

            stop_loss = technical_sl
            if (entry - stop_loss) < buffer:
                stop_loss = entry - buffer

            # Sanity Check (Min % distance)
            if (entry - stop_loss) / entry < min_stop_distance_pct:
                 stop_loss = entry * (1 - min_stop_distance_pct)

            risk = entry - stop_loss
            take_profit = entry + (risk * risk_reward_ratio)

        elif signal == "SHORT":
            technical_sl = invalidation
            volatility_sl = entry + buffer

            stop_loss = technical_sl
            if (stop_loss - entry) < buffer:
                stop_loss = entry + buffer

            if (stop_loss - entry) / entry < min_stop_distance_pct:
                stop_loss = entry * (1 + min_stop_distance_pct)

            risk = stop_loss - entry
            take_profit = entry - (risk * risk_reward_ratio)

        else:
            return None

        return {
            "entry": entry,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "side": signal,
            "setup_type": signal_data.get('type', 'Unknown')
        }
