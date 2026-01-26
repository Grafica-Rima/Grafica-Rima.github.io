import { useState, useEffect } from 'react'
import io from 'socket.io-client'
import './App.css'

const socket = io('http://localhost:8000', {
  transports: ['websocket', 'polling']
});

function App() {
  const [data, setData] = useState(null);
  const [searchInput, setSearchInput] = useState('');
  const [statusMsg, setStatusMsg] = useState('Connecting...');

  useEffect(() => {
    socket.on('connect', () => {
      setStatusMsg('Connected to Backend');
    });

    socket.on('status_update', (msg) => {
      setStatusMsg(msg.message);
    });

    socket.on('market_update', (newData) => {
      setData(newData);
    });

    return () => {
      socket.off('connect');
      socket.off('status_update');
      socket.off('market_update');
    };
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchInput.trim()) {
      socket.emit('request_pair_change', searchInput);
      setSearchInput('');
    }
  };

  // Determine styles based on state
  const isTradeActive = data?.state === 'IN_LONG' || data?.state === 'IN_SHORT';
  const signalColor = data?.state === 'IN_LONG' ? '#4caf50' : (data?.state === 'IN_SHORT' ? '#f44336' : '#eee');

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <h1 style={styles.title}>PRO TRADER AI</h1>
        <div style={styles.status}>{statusMsg}</div>
      </header>

      <div style={styles.mainContent}>
        {/* Search */}
        <form onSubmit={handleSearch} style={styles.searchForm}>
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search Pair (e.g. BTCUSDT.P)"
            style={styles.input}
          />
        </form>

        {/* Price Display */}
        <div style={styles.priceContainer}>
          <div style={styles.pairDisplay}>{data?.pair || '---'}</div>
          <div style={styles.priceDisplay}>
            {data?.current_price ? data.current_price.toFixed(2) : '---'}
          </div>
        </div>

        {/* Signal / Status */}
        <div style={styles.signalBox}>
          <h2 style={{margin: 0, color: '#888'}}>STATUS</h2>
          <div style={{...styles.stateText, color: signalColor}}>
            {data?.state || 'WAITING'}
          </div>
          <div style={styles.messageText}>{data?.message}</div>
        </div>

        {/* Trade Details (Fixed) */}
        {isTradeActive && data.trade_data && (
           <div style={styles.tradeGrid}>
             <div style={styles.tradeItem}>
                <span>ENTRY</span>
                <span style={styles.tradeValue}>{data.trade_data.entry?.toFixed(2)}</span>
             </div>
             <div style={styles.tradeItem}>
                <span>TP</span>
                <span style={{...styles.tradeValue, color: '#4caf50'}}>{data.trade_data.take_profit?.toFixed(2)}</span>
             </div>
             <div style={styles.tradeItem}>
                <span>SL</span>
                <span style={{...styles.tradeValue, color: '#f44336'}}>{data.trade_data.stop_loss?.toFixed(2)}</span>
             </div>
           </div>
        )}
      </div>
    </div>
  )
}

const styles = {
  container: {
    height: '100vh',
    width: '100vw',
    backgroundColor: '#121212',
    color: '#ffffff',
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    fontFamily: 'monospace',
    padding: '20px',
    boxSizing: 'border-box'
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid #333',
    paddingBottom: '10px',
    marginBottom: '20px'
  },
  title: {
    fontSize: '1.2rem',
    margin: 0,
    letterSpacing: '2px'
  },
  status: {
    fontSize: '0.8rem',
    color: '#666'
  },
  mainContent: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '40px'
  },
  searchForm: {
    marginBottom: '20px'
  },
  input: {
    background: 'transparent',
    border: '1px solid #444',
    padding: '10px 20px',
    color: '#fff',
    fontSize: '1rem',
    outline: 'none',
    textAlign: 'center',
    width: '300px'
  },
  priceContainer: {
    textAlign: 'center'
  },
  pairDisplay: {
    fontSize: '1.5rem',
    color: '#888',
    marginBottom: '10px'
  },
  priceDisplay: {
    fontSize: '5rem',
    fontWeight: 'bold',
    letterSpacing: '-2px'
  },
  signalBox: {
    textAlign: 'center'
  },
  stateText: {
    fontSize: '3rem',
    fontWeight: 'bold',
    marginTop: '10px'
  },
  messageText: {
    marginTop: '10px',
    color: '#aaa'
  },
  tradeGrid: {
    display: 'flex',
    gap: '50px',
    borderTop: '1px solid #333',
    paddingTop: '20px'
  },
  tradeItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '10px'
  },
  tradeValue: {
    fontSize: '1.5rem',
    fontWeight: 'bold'
  }
}

export default App
