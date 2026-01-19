
class StateManager:
    def __init__(self):
        self.active_trade = None  # None or Dict with keys: type, entry, sl, tp, symbol, timestamp

    def get_active_trade(self):
        return self.active_trade

    def set_active_trade(self, trade_data):
        """
        Sets a new trade.
        trade_data: {
            'type': 'LONG' or 'SHORT',
            'entry': float,
            'sl': float,
            'tp': float,
            'symbol': str,
            'reason': str
        }
        """
        if self.active_trade is not None:
            # Already have a trade, do not overwrite unless forced (logic handled elsewhere)
            return False
        self.active_trade = trade_data
        return True

    def close_trade(self):
        self.active_trade = None

    def check_exit(self, current_price):
        """
        Checks if current price hits SL or TP.
        Returns 'TP', 'SL', or None.
        """
        if not self.active_trade:
            return None

        trade = self.active_trade
        if trade['type'] == 'LONG':
            if current_price >= trade['tp']:
                return 'TP'
            if current_price <= trade['sl']:
                return 'SL'
        elif trade['type'] == 'SHORT':
            if current_price <= trade['tp']:
                return 'TP'
            if current_price >= trade['sl']:
                return 'SL'

        return None
