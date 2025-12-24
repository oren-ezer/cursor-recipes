import React from 'react'
import ReactDOM from 'react-dom/client'
import './index.css'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthProvider'
import { LanguageProvider, useLanguage } from './contexts/LanguageContext'
import MainLayout from './components/layout/MainLayout'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import RecipeListPage from './pages/RecipeListPage'
import MyRecipesPage from './pages/MyRecipesPage'
import RecipeDetailPage from './pages/RecipeDetailPage'
import RecipeCreatePage from './pages/RecipeCreatePage'
import RecipeEditPage from './pages/RecipeEditPage'
import TagSelectorDemo from './pages/TagSelectorDemo'
import PageContainer from './components/layout/PageContainer'
import ErrorBoundary from './components/ErrorBoundary'

// Placeholder Page Components
const HomePage = () => {
  const { t } = useLanguage();
  return (
    <PageContainer
      title={t('home.welcome')}
      description={t('home.description')}
    >
      <div className="text-center">
        <p className="text-lg text-gray-600 dark:text-gray-300">
          {t('home.get_started')}
        </p>
      </div>
    </PageContainer>
  );
};

const AboutPage = () => {
  const { t } = useLanguage();
  return (
    <PageContainer
      title={t('about.title')}
      description={t('about.description')}
    >
      <div className="text-center">
        <p className="text-lg text-gray-600 dark:text-gray-300">
          {t('about.content')}
        </p>
      </div>
    </PageContainer>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <LanguageProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/" element={<MainLayout><HomePage /></MainLayout>} />
              <Route path="/about" element={<MainLayout><AboutPage /></MainLayout>} />
              <Route path="/recipes" element={<RecipeListPage />} />
              <Route path="/recipes/new" element={<RecipeCreatePage />} />
              <Route path="/recipes/my" element={<MainLayout><MyRecipesPage /></MainLayout>} />
              <Route path="/recipes/:recipeId" element={<RecipeDetailPage />} />
              <Route path="/recipes/:recipeId/edit" element={<RecipeEditPage />} />
              <Route path="/my-recipes" element={<MainLayout><MyRecipesPage /></MainLayout>} />
              <Route path="/tag-selector-demo" element={<MainLayout><TagSelectorDemo /></MainLayout>} />
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </LanguageProvider>
    </ErrorBoundary>
  </React.StrictMode>,
)
