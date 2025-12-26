import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import LanguageSwitcher from '../LanguageSwitcher';

interface MainLayoutProps {
  children: React.ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const { isAuthenticated, user, logout } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();

  const isActivePath = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const getLinkClasses = (path: string) => {
    const baseClasses = "px-3 py-2 rounded-md text-sm font-medium transition-colors";
    const isActive = isActivePath(path);
    
    if (isActive) {
      return `${baseClasses} bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300`;
    }
    return `${baseClasses} text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-gray-700`;
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <nav className="bg-white dark:bg-gray-800 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-1">
              <Link to="/" className="font-semibold text-xl text-indigo-600 dark:text-indigo-400 px-3">
                {t('app.title')}
              </Link>
              <Link to="/" className={getLinkClasses('/')}>
                {t('nav.home')}
              </Link>
              <Link to="/about" className={getLinkClasses('/about')}>
                {t('nav.about')}
              </Link>
              <Link to="/recipes" className={getLinkClasses('/recipes')}>
                {t('nav.recipes')}
              </Link>
              {isAuthenticated && (
                <Link to="/my-recipes" className={getLinkClasses('/my-recipes')}>
                  {t('nav.my_recipes')}
                </Link>
              )}
              {isAuthenticated && user?.is_superuser && (
                <Link to="/admin" className={getLinkClasses('/admin')}>
                  {t('admin.title')}
                </Link>
              )}
            </div>
            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <>
                  <span className="text-sm text-gray-700 dark:text-gray-300">
                    {user?.email}
                  </span>
                  <button
                    onClick={handleLogout}
                    className="bg-red-500 hover:bg-red-600 text-white px-3 py-2 rounded-md text-sm font-medium"
                  >
                    {t('nav.logout')}
                  </button>
                </>
              ) : (
                <>
                  <Link to="/login" className="text-gray-700 dark:text-gray-300 hover:text-indigo-600 dark:hover:text-indigo-400 px-3 py-2 rounded-md text-sm font-medium">
                    {t('nav.login')}
                  </Link>
                  <Link to="/register" className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-2 rounded-md text-sm font-medium">
                    {t('nav.register')}
                  </Link>
                </>
              )}
              <div className="border-l border-gray-300 dark:border-gray-600 h-8"></div>
              <LanguageSwitcher />
            </div>
          </div>
        </div>
      </nav>

      <main>
        <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          {children}
        </div>
      </main>
    </div>
  );
};

export default MainLayout;
