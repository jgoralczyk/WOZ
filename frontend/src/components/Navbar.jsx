import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">System WOZ</div>
      <div className="navbar-links">
        <Link to="/" className="nav-link">Lista Wniosków</Link>
        <Link to="/create" className="btn-create">Create WOZ</Link>
      </div>
    </nav>
  );
}

export default Navbar;