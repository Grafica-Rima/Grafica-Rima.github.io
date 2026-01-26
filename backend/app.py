import socketio
from fastapi import FastAPI
from backend.data_handler import DataHandler
from backend.strategy import Strategy
from backend.risk_manager import RiskManager
from backend.state_manager import StateManager
from backend.config import Config
import asyncio

# Initialize Core Modules
data_handler = DataHandler()
strategy = Strategy()
risk_manager = RiskManager()
state_manager = StateManager()

# Global State
current_pair = Config.DEFAULT_PAIR

# Setup FastAPI and SocketIO
fastapi_app = FastAPI()
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
    global current_pair
    print(f"Request to change pair to: {new_pair}")

    # Simple normalization logic
    # User might type "btcusdt.p"
    clean = new_pair.upper().strip()
    if clean.endswith(".P"):
        clean = clean[:-2] # remove .P

    # Ensure slash if missing (simple heuristic)
    if "/" not in clean and "USDT" in clean:
        clean = clean.replace("USDT", "/USDT")

    current_pair = clean

    # Notify all clients
    await sio.emit('status_update', {'message': f'Switched to {current_pair}'})

async def trading_loop():
    """
    Main background loop.
    """
    global current_pair
    print("Starting Trading Loop...")

    while True:
        try:
            # 1. Fetch Data (Run in thread to avoid blocking event loop if sync)
            df = await asyncio.to_thread(data_handler.fetch_ohlcv, current_pair)

            if df is None or df.empty:
                await asyncio.sleep(2)
                continue

            current_price = df.iloc[-1]['close']

            # 2. Analyze
            # Strategy needs the dataframe
            signal = strategy.analyze(df)

            # 3. Risk Calculation (only if signal is active and we are searching)
            risk_params = {}
            if signal in ["LONG", "SHORT"]:
                risk_params = risk_manager.calculate_entry_params(signal, current_price, df)

            # 4. State Update
            status = state_manager.process_new_data(current_price, signal, risk_params)

            # Add pair info to status
            status['pair'] = current_pair

            # 5. Broadcast
            await sio.emit('market_update', status)

        except Exception as e:
            print(f"Error in trading loop: {e}")
            await sio.emit('error', {'message': str(e)})

        await asyncio.sleep(3) # Poll every 3 seconds

@fastapi_app.on_event("startup")
async def startup_event():
    asyncio.create_task(trading_loop())
