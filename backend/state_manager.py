class StateManager:
    def __init__(self):
        self.state = "SEARCHING" # SEARCHING, IN_LONG, IN_SHORT
        self.trade_data = {} # {entry, stop_loss, take_profit}

    def process_new_data(self, current_price, signal, risk_params):
        """
        Updates state based on price and potential new signal.

        current_price: float
        signal: "LONG", "SHORT", "NEUTRAL"
        risk_params: dict {entry, stop_loss, take_profit} calculated by RiskManager

        Returns the current status dictionary to be broadcasted.
        """
        message = ""

        # 1. Manage Active Trade
        if self.state == "IN_LONG":
            # Check TP/SL
            if current_price >= self.trade_data['take_profit']:
                self.state = "SEARCHING"
                message = f"TAKE PROFIT HIT (LONG) at {current_price}"
                self.trade_data = {}
            elif current_price <= self.trade_data['stop_loss']:
                self.state = "SEARCHING"
                message = f"STOP LOSS HIT (LONG) at {current_price}"
                self.trade_data = {}
            else:
                # Still in trade. Ignore new signals.
                pass

        elif self.state == "IN_SHORT":
             # Check TP/SL
            if current_price <= self.trade_data['take_profit']:
                self.state = "SEARCHING"
                message = f"TAKE PROFIT HIT (SHORT) at {current_price}"
                self.trade_data = {}
            elif current_price >= self.trade_data['stop_loss']:
                self.state = "SEARCHING"
                message = f"STOP LOSS HIT (SHORT) at {current_price}"
                self.trade_data = {}
            else:
                pass

        # 2. Check for New Trade (Only if SEARCHING)
        if self.state == "SEARCHING":
            if signal == "LONG":
                self.state = "IN_LONG"
                self.trade_data = risk_params
                message = f"OPEN LONG at {risk_params['entry']}"
            elif signal == "SHORT":
                self.state = "IN_SHORT"
                self.trade_data = risk_params
                message = f"OPEN SHORT at {risk_params['entry']}"

        return {
            "state": self.state,
            "trade_data": self.trade_data,
            "message": message,
            "current_price": current_price
        }
