import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function LoginPage() {
    const navigate = useNavigate();
    const { login, error } = useAuth();
    const [formData, setFormData] = useState({
        email: '',
        password: ''
    });
    const [loading, setLoading] = useState(false);
    const [localError, setLocalError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setLocalError('');

        const result = await login(formData.email, formData.password);

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
                    <div className="auth-logo">🔐</div>
                    <h1>Zaloguj się</h1>
                    <p>Witaj w systemie WOZ</p>
                </div>

                {(localError || error) && (
                    <div className="auth-error">
                        ⚠️ {localError || error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="auth-form">
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
                            placeholder="********"
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            required
                            autoComplete="current-password"
                        />
                    </div>

                    <button
                        type="submit"
                        className="btn-primary btn-full"
                        disabled={loading}
                    >
                        {loading ? 'Logowanie...' : 'Zaloguj się'}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Nie masz konta? <Link to="/register">Zarejestruj się</Link></p>
                </div>
            </div>
        </div>
    );
}

export default LoginPage;
