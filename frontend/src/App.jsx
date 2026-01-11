import { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [wnioski, setWnioski] = useState([]);
  const [currentUser, setCurrentUser] = useState('j.kowalski');
  const [role, setRole] = useState('user');

  // Funkcja pobierająca dane z Twojego FastAPI
  const fetchWnioski = async () => {
    try {
      const response = await axios.get('http://localhost:8000/wnioski/', {
        params: { user: currentUser, role: role }
      });
      setWnioski(response.data);
    } catch (error) {
      console.error("Błąd połączenia z API. Upewnij się, że FastAPI działa!", error);
    }
  };

  // useEffect odświeża listę, gdy zmienisz 'użytkownika' przyciskiem
  useEffect(() => {
    fetchWnioski();
  }, [currentUser, role]);

  return (
    <div style={{ padding: '40px', maxWidth: '1000px', margin: '0 auto', fontFamily: 'Arial' }}>
      <h1 style={{ color: '#2c3e50' }}>Panel Zarządzania Wnioskami</h1>

      {/* SYMULACJA LOGOWANIA */}
      <div style={{ background: '#ecf0f1', padding: '20px', borderRadius: '8px', marginBottom: '30px' }}>
        <h3>Zalogowany jako: <span style={{ color: '#2980b9' }}>{currentUser}</span> ({role})</h3>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => {setCurrentUser('j.kowalski'); setRole('user')}}>Jan (User)</button>
          <button onClick={() => {setCurrentUser('a.nowak'); setRole('user')}}>Anna (User)</button>
          <button onClick={() => {setCurrentUser('admin_payroll'); setRole('payroll')}}>Payroll (Admin)</button>
        </div>
      </div>

      {/* TABELA Z WNIOSKAMI */}
      <table style={{ width: '100%', borderCollapse: 'collapse', boxShadow: '0 1px 3px rgba(0,0,0,0.2)' }}>
        <thead>
          <tr style={{ background: '#34495e', color: 'white', textAlign: 'left' }}>
            <th style={{ padding: '12px' }}>ID</th>
            <th style={{ padding: '12px' }}>Tytuł</th>
            <th style={{ padding: '12px' }}>Kwota</th>
            <th style={{ padding: '12px' }}>Status</th>
            <th style={{ padding: '12px' }}>Właściciel</th>
          </tr>
        </thead>
        <tbody>
          {wnioski.map((w) => (
            <tr key={w.id} style={{ borderBottom: '1px solid #ddd' }}>
              <td style={{ padding: '12px' }}>{w.id}</td>
              <td style={{ padding: '12px' }}>{w.title}</td>
              <td style={{ padding: '12px' }}>{w.payoff} zł</td>
              <td style={{ padding: '12px' }}>
                <b style={{ color: w.status === 'Waiting' ? '#f39c12' : '#27ae60' }}>{w.status}</b>
              </td>
              <td style={{ padding: '12px' }}>{w.owner}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {wnioski.length === 0 && <p style={{ textAlign: 'center', marginTop: '20px' }}>Brak wniosków do wyświetlenia.</p>}
    </div>
  );
}

export default App;