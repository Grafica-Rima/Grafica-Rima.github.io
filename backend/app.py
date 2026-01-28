import socketio
from fastapi import FastAPI
from data_handler import DataHandler
from strategy import Strategy
from risk_manager import RiskManager
from state_manager import StateManager
from config import Config
from contextlib import asynccontextmanager
import asyncio
import pandas as pd

# Initialize Core Modules
data_handler = DataHandler()
strategy = Strategy()
risk_manager = RiskManager()
state_manager = StateManager()

# Global State
current_pair = Config.DEFAULT_PAIR
last_processed_candle = None # Timestamp

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Backend starting...")
    trading_task = asyncio.create_task(trading_loop())
    yield
    print("🛑 Backend shutting down...")
    trading_task.cancel()

# Setup FastAPI and SocketIO
fastapi_app = FastAPI(lifespan=lifespan)
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)

@fastapi_app.get("/")
def read_root():
    return {"status": "running", "pair": current_pair}

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('status_update', {'message': f'Connected. Monitoring {current_pair}'}, to=sid)

@sio.event
async def request_pair_change(sid, new_pair):
    global current_pair, last_processed_candle
    print(f"Request to change pair to: {new_pair}")

    clean = new_pair.upper().strip()
    if clean.endswith(".P"): clean = clean[:-2]
    if "/" not in clean and "USDT" in clean: clean = clean.replace("USDT", "/USDT")

    current_pair = clean
    last_processed_candle = None # Reset so we don't skip the first signal of the new pair

    await sio.emit('status_update', {'message': f'Switched to {current_pair}'})

async def trading_loop():
    """
    Main background loop.
    Refactored to check for candle CLOSES to avoid repainting.
    """
    global current_pair, last_processed_candle
    print("Starting Trading Loop...")

    while True:
        try:
            # 1. Fetch Data
            # We explicitly ask DataHandler to compute indicators (ATR/ADX)
            df = await asyncio.to_thread(data_handler.fetch_ohlcv, current_pair)

            # 2. Safety Check: Data Availability
            if df is None or df.empty:
                await sio.emit('status_update', {'message': 'DATA UNAVAILABLE - CHECK CONNECTION'})
                await asyncio.sleep(5)
                continue

            # Add Indicators here if not done in fetch (fetch calls add_indicators now)
            df = await asyncio.to_thread(data_handler.add_indicators, df)

            # 3. Candle Close Logic
            # We look at the second to last candle (iloc[-2]) because iloc[-1] is the OPEN/Current candle.
            # The signal must be confirmed on the CLOSED candle.

            # Current price is always needed for PnL/Display
            current_price = df.iloc[-1]['close']

            # The candle we analyze for signals is the LAST CLOSED ONE (iloc[-2])
            last_closed_candle = df.iloc[-2]
            closed_time = last_closed_candle['timestamp']

            signal = "NEUTRAL"

            # Only analyze strategy if we haven't processed this specific candle timestamp yet
            if last_processed_candle != closed_time:
                # 4. Analyze (Pass the WHOLE DF, strategy will look at history)
                # Strategy logic should strictly check df.iloc[-2] and back.
                signal = strategy.analyze(df)

                if signal != "NEUTRAL":
                     last_processed_candle = closed_time # Mark as processed so we don't re-enter

            # 5. Risk Calculation (Atomic with Signal)
            risk_params = {}
            if signal in ["LONG", "SHORT"]:
                # Pass ATR for dynamic SL
                atr = last_closed_candle.get('ATR', 0)
                risk_params = risk_manager.calculate_entry_params(signal, current_price, df, atr)

            # 6. State Update & Exit Management
            # StateManager handles exits (TP/SL) on every tick (using current_price)
            # But only accepts NEW entries if we passed a valid signal
            status = state_manager.process_new_data(current_price, signal, risk_params)

            # Add pair info to status
            status['pair'] = current_pair

            # 7. Broadcast
            await sio.emit('market_update', status)

        except Exception as e:
            print(f"Error in trading loop: {e}")
            await sio.emit('error', {'message': str(e)})

        await asyncio.sleep(3) # Poll every 3 seconds

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
