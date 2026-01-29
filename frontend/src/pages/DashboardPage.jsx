import { useState, useEffect } from 'react';

function DashboardPage() {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            const response = await fetch('http://localhost:8000/stats/');
            if (!response.ok) throw new Error('Błąd pobierania statystyk');
            const data = await response.json();
            setStats(data);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="dashboard-container">
                <div className="loading-spinner">Ładowanie statystyk...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="dashboard-container">
                <div className="error-message">⚠️ {error}</div>
            </div>
        );
    }

    const statusColors = {
        'Waiting': '#f59e0b',
        'Processing': '#3b82f6',
        'Completed': '#10b981',
        'Failed': '#ef4444',
        'Rejected': '#6b7280'
    };

    return (
        <div className="dashboard-container">
            <h1>📊 Dashboard</h1>

            <div className="stats-grid">
                {/* Główne statystyki */}
                <div className="stat-card stat-primary">
                    <div className="stat-icon">📄</div>
                    <div className="stat-content">
                        <div className="stat-value">{stats?.total_wnioski || 0}</div>
                        <div className="stat-label">Wszystkie wnioski</div>
                    </div>
                </div>

                <div className="stat-card stat-success">
                    <div className="stat-icon">💰</div>
                    <div className="stat-content">
                        <div className="stat-value">
                            {(stats?.total_payoff || 0).toLocaleString('pl-PL')} PLN
                        </div>
                        <div className="stat-label">Suma rozliczeń</div>
                    </div>
                </div>

                <div className="stat-card stat-info">
                    <div className="stat-icon">📈</div>
                    <div className="stat-content">
                        <div className="stat-value">
                            {(stats?.avg_payoff || 0).toLocaleString('pl-PL')} PLN
                        </div>
                        <div className="stat-label">Średnia wartość</div>
                    </div>
                </div>
            </div>

            {/* Status breakdown */}
            <div className="status-section">
                <h2>Wnioski według statusu</h2>
                <div className="status-grid">
                    {stats?.by_status && Object.entries(stats.by_status).map(([status, count]) => (
                        <div
                            key={status}
                            className="status-card"
                            style={{ borderLeftColor: statusColors[status] || '#6b7280' }}
                        >
                            <div className="status-count">{count}</div>
                            <div className="status-name">{status}</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Quick actions */}
            <div className="quick-actions">
                <h2>Szybkie akcje</h2>
                <div className="actions-grid">
                    <a href="/create" className="action-card">
                        <div className="action-icon">➕</div>
                        <div className="action-label">Nowy wniosek</div>
                    </a>
                    <a href="/" className="action-card">
                        <div className="action-icon">📋</div>
                        <div className="action-label">Lista wniosków</div>
                    </a>
                    <button onClick={fetchStats} className="action-card">
                        <div className="action-icon">🔄</div>
                        <div className="action-label">Odśwież</div>
                    </button>
                </div>
            </div>
        </div>
    );
}

export default DashboardPage;
