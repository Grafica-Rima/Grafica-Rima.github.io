import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import './index.css';

// Connect to Backend
const socket = io('http://localhost:8000');

function App() {
  const [symbol, setSymbol] = useState('BTC/USDT');
  const [searchInput, setSearchInput] = useState('');
  const [price, setPrice] = useState(0.0);
  const [prevPrice, setPrevPrice] = useState(0.0);
  const [status, setStatus] = useState({ state: 'SCANNING', trade: {} });

  useEffect(() => {
    // Socket Event Listeners
    socket.on('price_update', (data) => {
      if (data.symbol === symbol) {
        setPrevPrice((prev) => {
           // We can't access current price here reliably without ref,
           // but we just need previous render's price for color.
           // Actually, we can just use the previous state value provided by setState
           return prev;
        });
        setPrice((prev) => {
           setPrevPrice(prev); // Store current as previous before update
           return parseFloat(data.price);
        });
      }
    });

    socket.on('status_update', (data) => {
      setStatus(data);
    });

    socket.on('trade_update', (data) => {
      setStatus(data);
    });

    // Cleanup
    return () => {
      socket.off('price_update');
      socket.off('status_update');
      socket.off('trade_update');
    };
  }, [symbol]);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchInput) return;

    try {
      const response = await fetch('http://localhost:8000/set_symbol', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol: searchInput }),
      });
      const data = await response.json();
      if (data.status === 'ok') {
        setSymbol(data.symbol);
        setSearchInput('');
      } else {
        alert("Invalid Symbol or Error");
      }
    } catch (err) {
      console.error(err);
    }
  };

  const formatPrice = (p) => {
    return p ? p.toFixed(p < 1 ? 6 : 2) : '---';
  };

  const getPriceColor = () => {
    if (price > prevPrice) return 'price-up';
    if (price < prevPrice) return 'price-down';
    return '';
  };

  return (
    <div className="container">
      {/* Search Section */}
      <form className="search-box" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search Pair (e.g. BTC/USDT)"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
        />
        <button type="submit">SEARCH</button>
      </form>

      {/* Main Display */}
      <div>
        <h2 style={{color: '#888', letterSpacing: '2px'}}>{symbol} PERPETUAL</h2>
        <h1 className={`price-display ${getPriceColor()}`}>
          {formatPrice(price)}
        </h1>
      </div>

      {/* Signal / Status Section */}
      <div className={`signal-card ${status.state === 'IN_POSITION' ? `signal-${status.trade.type} signal-active` : ''}`}>
        {status.state === 'SCANNING' ? (
          <div className="status-scanning">
            <h2>SCANNING MARKETS...</h2>
            <p>Analyzing 5m Candles, Patterns, & Volume</p>
          </div>
        ) : (
          <>
            <div className="signal-header" style={{color: status.trade.type === 'LONG' ? '#4caf50' : '#f44336'}}>
              {status.trade.type} SIGNAL ACTIVE
            </div>

            <div className="trade-details">
              <div className="detail-item">
                <span className="label">ENTRY PRICE</span>
                <span className="value">{formatPrice(status.trade.entry_price)}</span>
              </div>
              <div className="detail-item">
                <span className="label">STOP LOSS</span>
                <span className="value" style={{color: '#f44336'}}>{formatPrice(status.trade.stop_loss)}</span>
              </div>
              <div className="detail-item">
                <span className="label">TAKE PROFIT</span>
                <span className="value" style={{color: '#4caf50'}}>{formatPrice(status.trade.take_profit)}</span>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default App;
