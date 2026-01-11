import { useState, useEffect } from 'react';

function ListPage() {
  const [wnioski, setWnioski] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/wnioski/')
      .then(res => res.json())
      .then(data => {
        // Zabezpieczenie: jeśli data nie jest tablicą, ustaw pustą listę
        setWnioski(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Problem z API:", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="container">Ładowanie danych...</div>;

  return (
    <div className="container">
      <h2>Złożone wnioski</h2>
      {wnioski.length === 0 ? (
        <p>Brak wniosków w bazie danych.</p>
      ) : (
        <div className="cards-grid">
          {wnioski.map(w => (
            <div key={w.id} className={`wniosek-card status-${(w.status || 'waiting').toLowerCase()}`}>
              <div className="card-header">
                <span className="badge">{w.status}</span>
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
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ListPage;