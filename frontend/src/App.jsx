
import { useState, useEffect } from 'react'
import io from 'socket.io-client'
import './App.css'

// Connect to backend (assumed to be on localhost:8000)
const socket = io('http://localhost:8000')

function App() {
  const [symbol, setSymbol] = useState('BTC/USDT')
  const [searchInput, setSearchInput] = useState('')
  const [price, setPrice] = useState(0.0)
  const [trade, setTrade] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState('Disconnected')

  useEffect(() => {
    socket.on('connect', () => {
      setConnectionStatus('Connected')
    })

    socket.on('disconnect', () => {
      setConnectionStatus('Disconnected')
    })

    socket.on('price_update', (data) => {
      if (data.symbol === symbol) {
        setPrice(data.price)
      }
    })

    socket.on('trade_signal', (data) => {
       // Data contains { type, entry, sl, tp, reason, symbol }
       if (data.symbol === symbol) {
         setTrade(data)
       }
    })

    socket.on('trade_update', (data) => {
       // { status: 'CLOSED', reason: 'TP' }
       if (data.status === 'CLOSED') {
         setTrade(null) // Clear trade or show closed status
         alert(`Trade Closed: ${data.reason}`)
       }
    })

    return () => {
      socket.off('connect')
      socket.off('disconnect')
      socket.off('price_update')
      socket.off('trade_signal')
      socket.off('trade_update')
    }
  }, [symbol])

  const handleSearch = async (e) => {
    e.preventDefault()
    // normalize input slightly
    let s = searchInput.toUpperCase().trim()
    // Basic heuristics to match backend expectations if user types "btcusdt"
    if (!s.includes('/') && s.length > 3) {
       // Try to guess split? No, let backend handle or user type correctly.
       // User prompt said "btcusdt.p", backend handles normalization.
    }

    try {
      const response = await fetch('http://localhost:8000/set_symbol', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: s })
      })
      const data = await response.json()
      if (data.status === 'ok') {
        setSymbol(data.symbol)
        setTrade(null) // Clear previous trade view
        setPrice(0)
      }
    } catch (error) {
      console.error("Error setting symbol:", error)
    }
  }

  // Styles
  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    backgroundColor: '#0f172a', // Dark slate
    color: '#e2e8f0', // Slate 200
    fontFamily: 'Inter, system-ui, sans-serif',
    overflow: 'hidden' // No scroll
  }

  const cardStyle = {
    backgroundColor: '#1e293b',
    padding: '2rem',
    borderRadius: '1rem',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    width: '400px',
    textAlign: 'center'
  }

  const priceStyle = {
    fontSize: '4rem',
    fontWeight: 'bold',
    margin: '1rem 0',
    color: '#38bdf8' // Sky 400
  }

  const signalBoxStyle = (type) => ({
    backgroundColor: type === 'LONG' ? '#064e3b' : '#7f1d1d', // Green/Red background
    padding: '1rem',
    borderRadius: '0.5rem',
    marginTop: '1.5rem',
    border: type === 'LONG' ? '1px solid #34d399' : '1px solid #f87171'
  })

  return (
    <div style={containerStyle}>
      <div style={cardStyle}>
        {/* Header / Search */}
        <div style={{ marginBottom: '2rem' }}>
          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="BTC/USDT..."
              style={{
                background: '#334155',
                border: 'none',
                padding: '0.5rem',
                borderRadius: '0.25rem',
                color: 'white',
                width: '100%'
              }}
            />
            <button type="submit" style={{
              background: '#3b82f6',
              border: 'none',
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              color: 'white',
              cursor: 'pointer'
            }}>
              Search
            </button>
          </form>
          <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginTop: '0.5rem' }}>
            Status: {connectionStatus} | Symbol: {symbol}
          </div>
        </div>

        {/* Price Display */}
        <div>
          <div style={{ fontSize: '1rem', color: '#cbd5e1' }}>CURRENT PRICE</div>
          <div style={priceStyle}>
            {price ? price.toFixed(price < 1 ? 4 : 2) : 'Loading...'}
          </div>
        </div>

        {/* Signal Dashboard */}
        {trade ? (
          <div style={signalBoxStyle(trade.type)}>
            <h2 style={{ margin: '0 0 1rem 0', color: trade.type === 'LONG' ? '#34d399' : '#f87171' }}>
              {trade.type} SIGNAL
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', textAlign: 'left' }}>
              <div>Entry:</div>
              <div style={{ fontWeight: 'bold' }}>{trade.entry}</div>

              <div>Stop Loss:</div>
              <div style={{ fontWeight: 'bold', color: '#f87171' }}>{trade.sl}</div>

              <div>Take Profit:</div>
              <div style={{ fontWeight: 'bold', color: '#34d399' }}>{trade.tp}</div>
            </div>
            <div style={{ marginTop: '1rem', fontSize: '0.8rem', fontStyle: 'italic' }}>
              Reason: {trade.reason}
            </div>
          </div>
        ) : (
          <div style={{ marginTop: '2rem', color: '#64748b' }}>
            Looking for signals...
          </div>
        )}

      </div>
    </div>
  )
}

export default App
