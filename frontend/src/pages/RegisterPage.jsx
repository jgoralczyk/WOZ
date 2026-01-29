import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function RegisterPage() {
    const navigate = useNavigate();
    const { register, error } = useAuth();
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        fullName: ''
    });
    const [loading, setLoading] = useState(false);
    const [localError, setLocalError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLocalError('');

        // Walidacja
        if (formData.password !== formData.confirmPassword) {
            setLocalError('Hasła nie są identyczne');
            return;
        }

        if (formData.password.length < 8) {
            setLocalError('Hasło musi mieć minimum 8 znaków');
            return;
        }

        setLoading(true);

        const result = await register(
            formData.email,
            formData.password,
            formData.fullName
        );

        setLoading(false);

        if (result.success) {
            navigate('/');
        } else {
            setLocalError(result.error);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <div className="auth-logo">📝</div>
                    <h1>Rejestracja</h1>
                    <p>Utwórz nowe konto w systemie WOZ</p>
                </div>

                {(localError || error) && (
                    <div className="auth-error">
                        ⚠️ {localError || error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-field">
                        <label>Imię i nazwisko</label>
                        <input
                            type="text"
                            placeholder="Jan Kowalski"
                            value={formData.fullName}
                            onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
                            required
                            autoComplete="name"
                        />
                    </div>

                    <div className="form-field">
                        <label>Email</label>
                        <input
                            type="email"
                            placeholder="twoj@email.pl"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            required
                            autoComplete="email"
                        />
                    </div>

                    <div className="form-field">
                        <label>Hasło</label>
                        <input
                            type="password"
                            placeholder="Minimum 8 znaków"
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            required
                            autoComplete="new-password"
                        />
                    </div>

                    <div className="form-field">
                        <label>Potwierdź hasło</label>
                        <input
                            type="password"
                            placeholder="Powtórz hasło"
                            value={formData.confirmPassword}
                            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                            required
                            autoComplete="new-password"
                        />
                    </div>

                    <button
                        type="submit"
                        className="btn-primary btn-full"
                        disabled={loading}
                    >
                        {loading ? 'Rejestracja...' : 'Zarejestruj się'}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Masz już konto? <Link to="/login">Zaloguj się</Link></p>
                </div>
            </div>
        </div>
    );
}

export default RegisterPage;
