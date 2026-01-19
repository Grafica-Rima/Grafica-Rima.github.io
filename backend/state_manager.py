class StateManager:
    def __init__(self):
        self.state = "SCANNING"  # SCANNING, IN_POSITION
        self.current_trade = {
            "symbol": None,
            "type": None,  # LONG or SHORT
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "status": None # OPEN, CLOSED
        }

    def reset_state(self):
        self.state = "SCANNING"
        self.current_trade = {
            "symbol": None,
            "type": None,
            "entry_price": None,
            "stop_loss": None,
            "take_profit": None,
            "status": None
        }

    def start_trade(self, symbol, trade_type, entry, sl, tp):
        if self.state == "IN_POSITION":
            return False # Already in a trade

        self.state = "IN_POSITION"
        self.current_trade = {
            "symbol": symbol,
            "type": trade_type,
            "entry_price": entry,
            "stop_loss": sl,
            "take_profit": tp,
            "status": "OPEN"
        }
        return True

    def update_trade_status(self, current_price):
        if self.state != "IN_POSITION":
            return None

        trade = self.current_trade
        result = None

        if trade["type"] == "LONG":
            if current_price >= trade["take_profit"]:
                result = "WIN"
            elif current_price <= trade["stop_loss"]:
                result = "LOSS"
        elif trade["type"] == "SHORT":
            if current_price <= trade["take_profit"]:
                result = "WIN"
            elif current_price >= trade["stop_loss"]:
                result = "LOSS"

        if result:
            self.state = "SCANNING" # Reset to scanning
            self.current_trade["status"] = "CLOSED"
            return result

        return "OPEN"

    def get_status(self):
        return {
            "state": self.state,
            "trade": self.current_trade
        }
