import React from 'react'
import ReactDOM from 'react-dom/client'
// import App from './App.tsx' // App is not used in this basic setup yet
import './index.css'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthProvider'; // Added AuthProvider import
import { useAuth } from './contexts/AuthContext'; // Added useAuth for example usage
import LoginPage from './pages/LoginPage'; // Added import for new LoginPage
import RegisterPage from './pages/RegisterPage'; // <-- Import the new RegisterPage

// Placeholder Page Components - now with auth example
const HomePage = () => {
  const { isAuthenticated, user, isLoading, logout } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-100 dark:bg-gray-900">
        <p className="text-xl text-gray-700 dark:text-gray-300">Loading auth status...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <nav className="bg-white dark:bg-gray-800 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <span className="font-semibold text-xl text-indigo-600 dark:text-indigo-400">MyApp</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/" className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 rounded-md text-sm font-medium">Home</Link>
              <Link to="/about" className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 rounded-md text-sm font-medium">About</Link>
              {isAuthenticated ? (
                <>
                  <span className="text-sm text-gray-700 dark:text-gray-300">Logged in as: {user?.email}</span>
                  <button 
                    onClick={logout} 
                    className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <Link to="/login" className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 rounded-md text-sm font-medium">Login</Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0 bg-white dark:bg-gray-800 shadow rounded-lg">
            <div className="p-4">
              <h1 className="text-3xl font-bold mb-4 text-center">Welcome to the Home Page!</h1>
              <p className="text-lg text-center">
                This is your application's main entry point. Explore and enjoy!
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

const AboutPage = () => {
  const { isAuthenticated, user, logout } = useAuth(); // Added for navbar consistency

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <nav className="bg-white dark:bg-gray-800 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <span className="font-semibold text-xl text-indigo-600 dark:text-indigo-400">MyApp</span>
            </div>
            <div className="flex items-center space-x-4">
              <Link to="/" className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 rounded-md text-sm font-medium">Home</Link>
              <Link to="/about" className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 rounded-md text-sm font-medium">About</Link>
              {isAuthenticated ? (
                <>
                  <span className="text-sm text-gray-700 dark:text-gray-300">Logged in as: {user?.email}</span>
                  <button 
                    onClick={logout} 
                    className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    Logout
                  </button>
                </>
              ) : (
                <Link to="/login" className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 rounded-md text-sm font-medium">Login</Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0 bg-white dark:bg-gray-800 shadow rounded-lg">
            <div className="p-4 text-center">
              <h1 className="text-3xl font-bold mb-4">About Page</h1>
              <p className="text-lg">
                This is the about page. Learn more about our application here!
              </p>
              <p className="mt-4 text-md">
                We aim to provide the best user experience.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

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
          <Route path="/register" element={<RegisterPage />} /> { /* <-- Added register route */ }
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>,
)
