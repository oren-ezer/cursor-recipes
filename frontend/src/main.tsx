import React from 'react'
import ReactDOM from 'react-dom/client'
// import App from './App.tsx' // App is not used in this basic setup yet
import './index.css'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthProvider'; // Added AuthProvider import
import { useAuth } from './contexts/AuthContext'; // Added useAuth for example usage
import LoginPage from './pages/LoginPage'; // Added import for new LoginPage

// Placeholder Page Components - now with auth example
const HomePage = () => {
  const { isAuthenticated, user, isLoading, logout } = useAuth();

  if (isLoading) return <p>Loading auth status...</p>;

  return (
    <div>
      <h1>Home Page</h1>
      <nav>
        <Link to="/">Home</Link> | <Link to="/about">About</Link>
        {isAuthenticated ? (
          <> | <span>Logged in as: {user?.email}</span> <button onClick={logout}>Logout</button></>
        ) : (
          <> | <Link to="/login">Login</Link></> // Assuming /login route will be created
        )}
      </nav>
      <p>Welcome to the home page!</p>
    </div>
  );
};

const AboutPage = () => (
  <div>
    <h1>About Page</h1>
    <nav>
      <Link to="/">Home</Link> | <Link to="/about">About</Link>
    </nav>
    <p>This is the about page.</p>
  </div>
);

// Placeholder Login Page (very basic) - REMOVED FROM HERE
// const LoginPage = () => { ... }; // This was the old placeholder

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider> { /* Added AuthProvider wrapper */ }
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/login" element={<LoginPage />} /> { /* Added login route */ }
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>,
)
