import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">🚗 System WOZ</Link>
      </div>

      <div className="navbar-links">
        <Link to="/dashboard" className="nav-link">📊 Dashboard</Link>
        <Link to="/" className="nav-link">📋 Wnioski</Link>
        <Link to="/create" className="btn-create">➕ Nowy</Link>
      </div>

      <div className="navbar-user">
        <span className="user-info">
          👤 {user?.full_name || user?.email}
          {user?.role && <span className="user-role">{user.role}</span>}
        </span>
        <button onClick={handleLogout} className="btn-logout">
          Wyloguj
        </button>
      </div>
    </nav>
  );
}

export default Navbar;