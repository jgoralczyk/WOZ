import { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext(null);

const API_URL = 'http://localhost:8000';

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // Sprawdź czy są zapisane tokeny przy starcie
    useEffect(() => {
        const accessToken = localStorage.getItem('accessToken');
        const savedUser = localStorage.getItem('user');

        if (accessToken && savedUser) {
            try {
                setUser(JSON.parse(savedUser));
            } catch (e) {
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                localStorage.removeItem('user');
            }
        }
        setLoading(false);
    }, []);

    const login = async (email, password) => {
        setError(null);
        try {
            const response = await fetch(`${API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Błąd logowania');
            }

            const data = await response.json();

            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('refreshToken', data.refresh_token);
            localStorage.setItem('user', JSON.stringify(data.user));

            setUser(data.user);
            return { success: true };
        } catch (err) {
            setError(err.message);
            return { success: false, error: err.message };
        }
    };

    const register = async (email, password, fullName) => {
        setError(null);
        try {
            const response = await fetch(`${API_URL}/auth/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    full_name: fullName
                })
            });

            if (!response.ok) {
                const data = await response.json();
                throw new Error(data.detail || 'Błąd rejestracji');
            }

            const data = await response.json();

            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('refreshToken', data.refresh_token);
            localStorage.setItem('user', JSON.stringify(data.user));

            setUser(data.user);
            return { success: true };
        } catch (err) {
            setError(err.message);
            return { success: false, error: err.message };
        }
    };

    const logout = () => {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        setUser(null);
    };

    const refreshToken = async () => {
        const refresh = localStorage.getItem('refreshToken');
        if (!refresh) {
            logout();
            return false;
        }

        try {
            const response = await fetch(`${API_URL}/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refresh })
            });

            if (!response.ok) {
                logout();
                return false;
            }

            const data = await response.json();
            localStorage.setItem('accessToken', data.access_token);
            localStorage.setItem('refreshToken', data.refresh_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            setUser(data.user);
            return true;
        } catch {
            logout();
            return false;
        }
    };

    // Helper do autoryzowanych requestów
    const authFetch = async (url, options = {}) => {
        const accessToken = localStorage.getItem('accessToken');

        const authOptions = {
            ...options,
            headers: {
                ...options.headers,
                'Authorization': `Bearer ${accessToken}`
            }
        };

        let response = await fetch(url, authOptions);

        // Jeśli 401, spróbuj odświeżyć token
        if (response.status === 401) {
            const refreshed = await refreshToken();
            if (refreshed) {
                const newToken = localStorage.getItem('accessToken');
                authOptions.headers['Authorization'] = `Bearer ${newToken}`;
                response = await fetch(url, authOptions);
            }
        }

        return response;
    };

    const value = {
        user,
        loading,
        error,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshToken,
        authFetch
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
}

export default AuthContext;
