import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import ListPage from './pages/ListPage';
import FormPage from './pages/FormPage';
import './App.css';
import './Index.css';

function App() {
  return (
    <Router>
      <div className="app-shell">
        <Navbar />
        {/* TO JEST KLUCZOWY ELEMENT POD NAVBARem */}
        <main className="content-area">
          <Routes>
            <Route path="/" element={<ListPage />} />
            <Route path="/create" element={<FormPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;