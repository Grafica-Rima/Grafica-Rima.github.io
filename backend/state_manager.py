
class StateManager:
    def __init__(self):
        self.current_trade = None # { status: "OPEN" | "WAITING", data: { ... } }
        self.reset_state()

    def reset_state(self):
        self.current_trade = {
            "status": "WAITING",
            "data": None
        }

    def process_signal(self, trade_params, current_price):
        """
        Manages state transitions.
        CRITICAL: If a trade is OPEN, do NOT change Entry/SL/TP.
        """
        if self.current_trade['status'] == "WAITING":
            if trade_params:
                # Enter new trade
                print(f"Entering Trade: {trade_params}")
                self.current_trade['status'] = "OPEN"
                self.current_trade['data'] = trade_params
                return self.current_trade

        elif self.current_trade['status'] == "OPEN":
            # Check for Exit conditions
            trade = self.current_trade['data']
            side = trade['side']
            sl = trade['stop_loss']
            tp = trade['take_profit']

            # Check TP/SL hit
            if side == "LONG":
                if current_price >= tp:
                    print("Take Profit Hit (LONG)")
                    self.reset_state()
                elif current_price <= sl:
                    print("Stop Loss Hit (LONG)")
                    self.reset_state()
            elif side == "SHORT":
                if current_price <= tp:
                    print("Take Profit Hit (SHORT)")
                    self.reset_state()
                elif current_price >= sl:
                    print("Stop Loss Hit (SHORT)")
                    self.reset_state()

            # If still open, return the FIXED trade data. Do not update it with new signals.
            return self.current_trade

        return self.current_trade
