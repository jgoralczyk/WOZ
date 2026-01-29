import { useState, useEffect } from 'react';

function ListPage() {
  const [wnioski, setWnioski] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentUser, setCurrentUser] = useState('default_user');
  const [currentRole, setCurrentRole] = useState('payroll'); // 'user' lub 'payroll'

  const fetchWnioski = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `http://localhost:8000/wnioski/?user=${encodeURIComponent(currentUser)}&role=${currentRole}`
      );
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setWnioski(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error("Problem z API:", err);
      setError(err.message);
      setWnioski([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWnioski();
  }, [currentUser, currentRole]);

  const getStatusClass = (status) => {
    const statusLower = (status || 'waiting').toLowerCase();
    const statusMap = {
      'waiting': 'status-waiting',
      'processing': 'status-processing',
      'completed': 'status-completed',
      'failed': 'status-failed',
      'rejected': 'status-rejected'
    };
    return statusMap[statusLower] || 'status-waiting';
  };

  const getStatusEmoji = (status) => {
    const statusLower = (status || 'waiting').toLowerCase();
    const emojiMap = {
      'waiting': '⏳',
      'processing': '⚙️',
      'completed': '✅',
      'failed': '❌',
      'rejected': '🚫'
    };
    return emojiMap[statusLower] || '⏳';
  };

  return (
    <div className="container">
      {/* Filters */}
      <div className="filters-bar">
        <div className="filter-group">
          <label>Użytkownik:</label>
          <input 
            type="text" 
            value={currentUser} 
            onChange={(e) => setCurrentUser(e.target.value)}
            placeholder="Nazwa użytkownika"
          />
        </div>
        <div className="filter-group">
          <label>Rola:</label>
          <select value={currentRole} onChange={(e) => setCurrentRole(e.target.value)}>
            <option value="user">Użytkownik (tylko moje)</option>
            <option value="payroll">Payroll (wszystkie)</option>
          </select>
        </div>
        <button onClick={fetchWnioski} className="btn-refresh">
          🔄 Odśwież
        </button>
      </div>

      <h2>Złożone wnioski</h2>

      {loading && <div className="loading-spinner">Ładowanie danych...</div>}
      
      {error && (
        <div className="error-message">
          ⚠️ Błąd pobierania danych: {error}
          <button onClick={fetchWnioski}>Spróbuj ponownie</button>
        </div>
      )}
      
      {!loading && !error && wnioski.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📭</div>
          <p>Brak wniosków w bazie danych.</p>
        </div>
      )}
      
      {!loading && !error && wnioski.length > 0 && (
        <div className="cards-grid">
          {wnioski.map(w => (
            <div key={w.id} className={`wniosek-card ${getStatusClass(w.status)}`}>
              <div className="card-header">
                <span className="badge">
                  {getStatusEmoji(w.status)} {w.status}
                </span>
                <span className="date">
                  {w.created_date ? new Date(w.created_date).toLocaleDateString('pl-PL') : 'Brak daty'}
                </span>
              </div>
              <h3>{w.title || "Bez tytułu"}</h3>
              <div className="card-details">
                <p>👤 <strong>{w.person}</strong></p>
                <p>🏢 {w.company}</p>
                <p>🚗 {w.type_of_woz}</p>
                <p className="price">{(w.payoff || 0).toLocaleString('pl-PL')} PLN</p>
              </div>
              {w.status === 'Completed' && (
                <div className="card-actions">
                  <a 
                    href={`http://localhost:8000/wnioski/${w.id}/pdf`} 
                    className="btn-download"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    📥 Pobierz PDF
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ListPage;