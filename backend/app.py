import asyncio
import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from config import HOST, PORT, SYMBOL, TIMEFRAME
from data_handler import DataHandler
from strategy import Strategy
from risk_manager import RiskManager
from state_manager import StateManager

# --- Initialize Components ---
app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

# Allow CORS for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_handler = DataHandler()
strategy = Strategy()
risk_manager = RiskManager()
state_manager = StateManager()

# Default Symbol
current_symbol = SYMBOL
data_handler.set_symbol(current_symbol)

# --- Background Task for Real-time Analysis ---
async def market_loop():
    print("Starting Market Loop...")
    while True:
        try:
            # 1. Fetch Data
            # Fetch Current Price for live updates and State Management
            current_price = await data_handler.fetch_current_price()

            # Fetch Candles for Strategy Analysis (Last closed candle priority)
            df = await data_handler.fetch_ohlcv(limit=100)

            # 2. Update State (Check SL/TP)
            # This must be done on every tick (or frequently)
            trade_status_result = state_manager.update_trade_status(current_price)

            if trade_status_result in ["WIN", "LOSS"]:
                # Trade Closed
                print(f"Trade Closed: {trade_status_result}")
                await sio.emit('trade_update', state_manager.get_status())

            # 3. Strategy Execution (Only if SCANNING)
            status = state_manager.get_status()
            if status['state'] == "SCANNING" and df is not None:
                signal, details = strategy.analyze(df)

                if signal:
                    print(f"Signal Detected: {signal}")
                    entry_price = details['close_price'] # Assume entry at close of signal candle
                    sr_levels = details['sr_levels']
                    fib_levels = details['fib_levels']

                    sl, tp = risk_manager.calculate_sl_tp(signal, entry_price, sr_levels, fib_levels)

                    # Fix values and enter trade state
                    success = state_manager.start_trade(current_symbol, signal, entry_price, sl, tp)
                    if success:
                        print(f"Trade Started: {signal} @ {entry_price} | SL: {sl} | TP: {tp}")
                        await sio.emit('trade_update', state_manager.get_status())

            # 4. Emit Real-time Data to Frontend
            await sio.emit('price_update', {'symbol': current_symbol, 'price': current_price})
            await sio.emit('status_update', state_manager.get_status())

        except Exception as e:
            print(f"Error in market loop: {e}")

        # Sleep interval
        # Ideally, we stream via websocket, but for this loop we poll.
        # 5-minute candle logic implies we check strategy on close, but we need price updates faster.
        await asyncio.sleep(2) # 2 second poll for price updates

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "running"}

@app.post("/set_symbol")
async def set_symbol(data: dict):
    global current_symbol
    new_symbol = data.get("symbol")
    if new_symbol:
        # Reset state when changing symbol?
        # User said "Quiero que el frontend tenga una caja de búsqueda...".
        # Usually changing symbol implies resetting analysis.
        current_symbol = new_symbol.upper()
        data_handler.set_symbol(current_symbol)
        state_manager.reset_state() # Reset active trade if any? Or keep it running?
        # Safer to reset or the user gets confused seeing BTC trade on ETH chart.
        return {"status": "ok", "symbol": current_symbol}
    return {"status": "error"}

@sio.event
async def connect(sid, environ):
    print("Client connected", sid)
    # Send initial state
    await sio.emit('status_update', state_manager.get_status())

@sio.event
async def disconnect(sid):
    print("Client disconnected", sid)

# --- Startup & Shutdown ---
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(market_loop())

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down...")
    await data_handler.close_exchange()

if __name__ == "__main__":
    uvicorn.run("app:socket_app", host=HOST, port=PORT, reload=True)
