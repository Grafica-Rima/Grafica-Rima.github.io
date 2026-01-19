
import asyncio
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import socketio
from config import Config
from data_handler import DataHandler
from strategy import Strategy
from risk_manager import RiskManager
from state_manager import StateManager
from pydantic import BaseModel

# --- App Setup ---
app = FastAPI()

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Socket.IO Setup
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

# Modules
data_handler = DataHandler()
strategy = Strategy()
risk_manager = RiskManager(atr_multiplier_sl=Config.SL_ATR_MULTIPLIER, risk_reward_ratio=Config.RISK_REWARD_RATIO)
state_manager = StateManager()

current_symbol = Config.SYMBOL_DEFAULT
is_running = True

# --- Models ---
class SymbolRequest(BaseModel):
    symbol: str

# --- Routes ---
@app.get("/")
def read_root():
    return {"status": "active", "symbol": current_symbol}

@app.post("/set_symbol")
async def set_symbol(req: SymbolRequest):
    global current_symbol
    # Simple validation/formatting
    s = req.symbol.upper()
    if not '/' in s and not 'USDT' in s:
        s += '/USDT' # Default assumption if user types just 'BTC'

    # Handle the ".p" request from user (e.g. btcusdt.p) to convert to CCXT format if needed
    # CCXT usually takes 'BTC/USDT' for swap if configured correctly.
    # We will normalize inputs like 'btcusdt.p' -> 'BTC/USDT' (and rely on the exchange options in data_handler to select Swap)

    # Simple normalizer
    s = s.replace('USDT.P', '/USDT').replace('USDT', '/USDT').replace('//', '/')
    if s.endswith('.P'):
        s = s.replace('.P', '') # Remove .p suffix if it remains
        if '/' not in s:
             # Assume last 3-4 chars are quote, but user said 'riverusdt.p'
             # Let's just try to be smart or expect standard format.
             # If user types 'btcusdt', we make it 'BTC/USDT'.
             pass

    # Better: just trust the DataHandler to try to fetch it, or update current_symbol
    current_symbol = s
    # Reset trade state on symbol change? Maybe not if we want to track the old one, but for this app: yes.
    state_manager.close_trade()
    return {"status": "ok", "symbol": current_symbol}

# --- Background Task for Analysis ---
async def market_loop():
    print("Starting Market Loop...")
    while is_running:
        try:
            # 1. Get Real-time Price for UI
            price = await data_handler.get_latest_price(current_symbol)
            if price:
                await sio.emit('price_update', {'symbol': current_symbol, 'price': price})

                # 2. Check Active Trade Exit
                exit_signal = state_manager.check_exit(price)
                if exit_signal:
                    print(f"Trade Closed: {exit_signal}")
                    state_manager.close_trade()
                    await sio.emit('trade_update', {'status': 'CLOSED', 'reason': exit_signal})

            # 3. Fetch Candles & Analyze (Periodically, e.g. every 10 seconds check if we need new calculation)
            # Ideally this runs on candle close, but polling is safer for MVP.
            df = await data_handler.fetch_ohlcv(current_symbol, limit=100)

            # 4. Strategy Analysis
            analysis = strategy.analyze(df)

            # 5. Signal Handling
            if analysis:
                active_trade = state_manager.get_active_trade()

                # If no active trade, look for new signals
                if not active_trade and analysis['signal']:
                    tp, sl = risk_manager.calculate_tp_sl(
                        analysis['signal'],
                        analysis['close'],
                        analysis['atr'],
                        support=analysis['support'],
                        resistance=analysis['resistance']
                    )

                    new_trade = {
                        'type': analysis['signal'],
                        'entry': analysis['close'],
                        'sl': sl,
                        'tp': tp,
                        'symbol': current_symbol,
                        'reason': analysis['reason'],
                        'timestamp': str(df.index[-1])
                    }

                    if state_manager.set_active_trade(new_trade):
                        print(f"New Signal: {new_trade}")
                        await sio.emit('trade_signal', new_trade)

                # If active trade exists, just emit its status (so frontend is synced)
                elif active_trade:
                     await sio.emit('trade_signal', active_trade) # Re-emit current trade state

            # Sleep to avoid rate limits
            await asyncio.sleep(5)

        except Exception as e:
            print(f"Error in market loop: {e}")
            await asyncio.sleep(5)

# --- Events ---
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(market_loop())

@app.on_event("shutdown")
async def shutdown_event():
    await data_handler.close()

# Start with: uvicorn app:socket_app --reload
