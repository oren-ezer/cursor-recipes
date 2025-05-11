import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthProvider'
import MainLayout from './components/layout/MainLayout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import RecipeListPage from './pages/RecipeListPage'
import MyRecipesPage from './pages/MyRecipesPage'
import PageContainer from './components/layout/PageContainer'

// Placeholder Page Components
const HomePage = () => {
  return (
    <PageContainer
      title="Welcome to Recipe App"
      description="Discover, create, and share your favorite recipes with the world."
    >
      <div className="text-center">
        <p className="text-lg text-gray-600 dark:text-gray-300">
          Get started by exploring recipes or creating your own!
        </p>
      </div>
    </PageContainer>
  );
};

const AboutPage = () => {
  return (
    <PageContainer
      title="About Recipe App"
      description="Learn more about our mission and features."
    >
      <div className="text-center">
        <p className="text-lg text-gray-600 dark:text-gray-300">
          We aim to provide the best recipe sharing experience.
        </p>
      </div>
    </PageContainer>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainLayout><HomePage /></MainLayout>} />
          <Route path="/about" element={<MainLayout><AboutPage /></MainLayout>} />
          <Route path="/recipes" element={<RecipeListPage />} />
          <Route path="/my-recipes" element={<MainLayout><MyRecipesPage /></MainLayout>} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>,
)
