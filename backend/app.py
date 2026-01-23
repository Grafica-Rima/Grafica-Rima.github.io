
import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import socketio
import uvicorn
from contextlib import asynccontextmanager

from data_handler import DataHandler
from strategy import Strategy
from risk_manager import RiskManager
from state_manager import StateManager
from config import SOCKET_SERVER_URL, DEFAULT_PAIR

# Socket.IO setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
# REMOVE THIS LINE: socket_app = socketio.ASGIApp(sio)
# We will mount it differently or just let it be if using just socketio

# Core Components
data_handler = DataHandler()
strategy = Strategy()
risk_manager = RiskManager()
state_manager = StateManager()

running = True
current_symbol = DEFAULT_PAIR

async def trading_loop():
    """
    Main background loop:
    1. Fetch Data (5m and 1h)
    2. Analyze
    3. Manage State
    4. Broadcast
    """
    global current_symbol
    print("Starting Trading Loop...")

    # Initialize connection
    await data_handler.initialize()
    if data_handler.mock_mode:
        print("Using Mock Data Source")

    while running:
        try:
            # 1. Fetch Price & Candles (5m and 1h)
            price = await data_handler.fetch_current_price(current_symbol)
            candles_5m = await data_handler.fetch_candles(current_symbol, timeframe='5m')
            candles_1h = await data_handler.fetch_candles(current_symbol, timeframe='1h')

            trade_info = None

            if price is not None and not candles_5m.empty:
                # 2. Analyze Strategy (Pass both timeframes)
                signal_data = strategy.analyze(candles_5m, candles_1h)

                # 3. Calculate Risk & Manage State
                trade_params = None
                if signal_data:
                    trade_params = risk_manager.calculate_trade_params(signal_data)

                state_result = state_manager.process_signal(trade_params, price)

                # Prepare payload
                payload = {
                    "symbol": current_symbol,
                    "price": price,
                    "state": state_result['status'],
                    "trade": state_result['data'],
                    "signal_debug": signal_data['type'] if signal_data else None
                }

                # 4. Broadcast
                # print(f"Broadcast: {payload}")
                await sio.emit('market_update', payload)

            await asyncio.sleep(2) # 2 second refresh rate

        except Exception as e:
            print(f"Error in loop: {e}")
            await asyncio.sleep(5)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    loop_task = asyncio.create_task(trading_loop())
    yield
    # Shutdown
    global running
    running = False
    await data_handler.close()
    loop_task.cancel()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/set_symbol")
async def set_symbol(symbol: str):
    global current_symbol
    # Validate
    valid_symbol = await data_handler.validate_symbol(symbol)
    if valid_symbol:
        current_symbol = valid_symbol
        state_manager.reset_state()
        return {"status": "success", "symbol": current_symbol}
    else:
        return {"status": "error", "message": "Invalid Symbol"}

# Mount Socket.IO AFTER other routes to avoid it catching everything
socket_app = socketio.ASGIApp(sio, app)

if __name__ == "__main__":
    # We must run the socket_app which wraps the FastAPI app
    uvicorn.run("app:socket_app", host="0.0.0.0", port=8000, reload=True)
