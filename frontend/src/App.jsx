import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import ListPage from './pages/ListPage';
import FormPage from './pages/FormPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import './App.css';

// Protected Route component
function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="loading-spinner">Ładowanie...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

// Public Route (redirect if already logged in)
function PublicRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return <div className="loading-spinner">Ładowanie...</div>;
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return children;
}

function AppContent() {
  const { isAuthenticated } = useAuth();

  return (
    <div className="app-shell">
      {isAuthenticated && <Navbar />}
      <main className={`content-area ${!isAuthenticated ? 'full-height' : ''}`}>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={
            <PublicRoute>
              <LoginPage />
            </PublicRoute>
          } />
          <Route path="/register" element={
            <PublicRoute>
              <RegisterPage />
            </PublicRoute>
          } />

          {/* Protected routes */}
          <Route path="/" element={
            <ProtectedRoute>
              <ListPage />
            </ProtectedRoute>
          } />
          <Route path="/create" element={
            <ProtectedRoute>
              <FormPage />
            </ProtectedRoute>
          } />
          <Route path="/dashboard" element={
            <ProtectedRoute>
              <DashboardPage />
            </ProtectedRoute>
          } />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}

export default App;