import { useState, useEffect } from 'react'
import io from 'socket.io-client'
import './App.css'

const socket = io('http://localhost:8000')

function App() {
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [currentPrice, setCurrentPrice] = useState(0)
  const [tradeState, setTradeState] = useState('WAITING')
  const [tradeData, setTradeData] = useState(null)
  const [debugSignal, setDebugSignal] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('Disconnected')
  const [searchInput, setSearchInput] = useState('')

  useEffect(() => {
    socket.on('connect', () => setConnectionStatus('Connected'))
    socket.on('disconnect', () => setConnectionStatus('Disconnected'))

    socket.on('market_update', (data) => {
      // data = { symbol, price, state, trade, signal_debug }
      if (data.symbol === symbol) {
        setCurrentPrice(data.price)
        setTradeState(data.state)
        setTradeData(data.trade)
        setDebugSignal(data.signal_debug)
      }
    })

    return () => {
      socket.off('connect')
      socket.off('disconnect')
      socket.off('market_update')
    }
  }, [symbol])

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!searchInput) return

    try {
      const response = await fetch(`http://localhost:8000/set_symbol?symbol=${searchInput}`, {
        method: 'POST'
      })
      const result = await response.json()
      if (result.status === 'success') {
        setSymbol(result.symbol)
        setSearchInput('')
      } else {
        alert('Invalid Symbol')
      }
    } catch (err) {
      console.error(err)
      alert('Error connecting to backend')
    }
  }

  return (
    <div className="app-container">
      <header className="header">
        <div className={`status-indicator ${connectionStatus === 'Connected' ? 'green' : 'red'}`}>
          {connectionStatus}
        </div>
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search Pair (e.g. BTC/USDT, ETH/USDT.P)"
            className="search-input"
          />
          <button type="submit" className="search-button">GO</button>
        </form>
      </header>

      <main className="main-content">
        <div className="price-section">
          <h1 className="symbol-title">{symbol}</h1>
          <div className="price-display">
            {currentPrice ? currentPrice.toFixed(2) : 'Loading...'}
          </div>
        </div>

        <div className="signal-section">
          <div className={`signal-card ${tradeState === 'OPEN' ? (tradeData?.side === 'LONG' ? 'bg-green' : 'bg-red') : 'bg-gray'}`}>
            <h2>STATUS: {tradeState}</h2>

            {tradeState === 'OPEN' && tradeData && (
              <div className="trade-details">
                <div className="trade-row">
                  <span>SIDE:</span>
                  <span className="bold">{tradeData.side}</span>
                </div>
                <div className="trade-row">
                  <span>SETUP:</span>
                  <span className="small-text">{tradeData.setup_type}</span>
                </div>
                <div className="trade-row">
                  <span>ENTRY:</span>
                  <span>{tradeData.entry.toFixed(2)}</span>
                </div>
                <div className="trade-row">
                  <span>TAKE PROFIT:</span>
                  <span>{tradeData.take_profit.toFixed(2)}</span>
                </div>
                <div className="trade-row">
                  <span>STOP LOSS:</span>
                  <span>{tradeData.stop_loss.toFixed(2)}</span>
                </div>
              </div>
            )}

            {tradeState === 'WAITING' && (
              <p className="waiting-text">Scanning for signals...</p>
            )}

            {debugSignal && (
               <div className="debug-info">Last Pattern: {debugSignal}</div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
