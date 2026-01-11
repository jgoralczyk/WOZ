import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

function FormPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '', person: '', company: '', type_of_woz: '', payoff: 0, billing_month: '', comment: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const payload = { ...formData, payoff: parseFloat(formData.payoff), billing_month: `${formData.billing_month}-01` };

    const response = await fetch('http://localhost:8000/wnioski/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (response.ok) navigate('/');
  };

  return (
    <div className="form-container">
      <section className="form-card">
        <header className="form-header">
          <h2>Nowy Wniosek WOZ</h2>
          <p>Wypełnij wszystkie dane, aby przesłać wniosek do przetworzenia.</p>
        </header>

        <form onSubmit={handleSubmit} className="elegant-form">
          {/* Tytuł na pełną szerokość */}
          <div className="form-field full-width">
            <label>Tytuł wniosku</label>
            <input type="text" placeholder="np. Rozliczenie transportu międzynarodowego" required
              onChange={e => setFormData({...formData, title: e.target.value})} />
          </div>

          {/* Dwie kolumny */}
          <div className="form-row">
            <div className="form-field">
              <label>Osoba odpowiedzialna</label>
              <input type="text" placeholder="Imię i nazwisko" required
                onChange={e => setFormData({...formData, person: e.target.value})} />
            </div>
            <div className="form-field">
              <label>Firma / Kontrahent</label>
              <input type="text" placeholder="Nazwa firmy" required
                onChange={e => setFormData({...formData, company: e.target.value})} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label>Typ pojazdu / WOZ</label>
              <input type="text" placeholder="np. Standard, Mega, Chłodnia" required
                onChange={e => setFormData({...formData, type_of_woz: e.target.value})} />
            </div>
            <div className="form-field">
              <label>Kwota rozliczenia (PLN)</label>
              <input type="number" step="0.01" placeholder="0.00" required
                onChange={e => setFormData({...formData, payoff: e.target.value})} />
            </div>
          </div>

          <div className="form-row">
            <div className="form-field">
              <label>Miesiąc rozliczeniowy</label>
              <input type="month" required
                onChange={e => setFormData({...formData, billing_month: e.target.value})} />
            </div>
          </div>

          {/* Komentarz na pełną szerokość */}
          <div className="form-field full-width">
            <label>Dodatkowy komentarz</label>
            <textarea placeholder="Wpisz dodatkowe uwagi (opcjonalnie)..." rows="4"
              onChange={e => setFormData({...formData, comment: e.target.value})} />
          </div>

          <div className="form-actions">
             <button type="button" className="btn-secondary" onClick={() => navigate('/')}>Anuluj</button>
             <button type="submit" className="btn-primary">Złóż wniosek</button>
          </div>
        </form>
      </section>
    </div>
  );
}

export default FormPage;