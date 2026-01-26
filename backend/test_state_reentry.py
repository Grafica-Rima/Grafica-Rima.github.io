
import unittest
from datetime import datetime, timedelta
from state_manager import StateManager

class TestStateReentry(unittest.TestCase):
    def setUp(self):
        self.state_manager = StateManager()

    def test_reentry_prevention(self):
        # 1. Signal at T1
        ts1 = datetime(2023, 1, 1, 10, 0, 0)
        params = {
            "side": "LONG",
            "entry": 100.0,
            "stop_loss": 90.0,
            "take_profit": 120.0
        }

        # Process Signal (Entry)
        res = self.state_manager.process_signal(params, 100.0, ts1)
        self.assertEqual(res['status'], "OPEN")
        self.assertEqual(self.state_manager.last_trade_candle_timestamp, ts1)

        # 2. Price hits Stop Loss immediately
        res = self.state_manager.process_signal(None, 89.0, ts1) # Update price
        self.assertEqual(res['status'], "WAITING") # Trade Closed

        # 3. Same Signal at T1 comes again (Trading loop runs often)
        # Should be ignored
        res = self.state_manager.process_signal(params, 95.0, ts1)
        self.assertEqual(res['status'], "WAITING") # Still waiting, did not re-enter

        # 4. New Signal at T2 (Next Candle)
        ts2 = datetime(2023, 1, 1, 10, 5, 0)
        res = self.state_manager.process_signal(params, 95.0, ts2)
        self.assertEqual(res['status'], "OPEN") # Entered new trade
        self.assertEqual(self.state_manager.last_trade_candle_timestamp, ts2)

if __name__ == '__main__':
    unittest.main()
