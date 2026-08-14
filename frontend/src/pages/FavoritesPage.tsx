import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Heart } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';
import { apiClient } from '../lib/api-client';
import type { Recipe } from '../lib/api-client';
import { useAuth } from '../contexts/AuthContext';
import PageContainer from '../components/layout/PageContainer';
import RecipeCard from '../components/RecipeCard';

const FavoritesPage: React.FC = () => {
  const { t } = useLanguage();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate('/login');
      return;
    }

    if (isAuthenticated) {
      fetchFavorites();
    }
  }, [isAuthenticated, authLoading, navigate]);

  const fetchFavorites = async () => {
    setIsLoading(true);
    setError(null);
    try {
      // First get favorite recipe IDs
      const favoriteIds = await apiClient.getMyFavorites();
      
      if (favoriteIds.length === 0) {
        setRecipes([]);
        setIsLoading(false);
        return;
      }
      
      // Since we don't have a bulk fetch endpoint, we'll fetch them individually for now
      // A better approach would be to create a `/recipes/bulk` or `/recipes/favorites` endpoint that returns Recipe objects
      const recipePromises = favoriteIds.map(id => apiClient.getRecipe(id).catch(e => {
        console.error(`Failed to fetch recipe ${id}:`, e);
        return null;
      }));
      
      const results = await Promise.all(recipePromises);
      const validRecipes = results.filter((r): r is Recipe => r !== null);
      
      setRecipes(validRecipes);
    } catch (err) {
      console.error('Failed to load favorites:', err);
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  if (authLoading || isLoading) {
    return (
      <PageContainer title={t('interactions.favorites.title')}>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer title={t('interactions.favorites.title')}>
      {error && (
        <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg">
          {error}
        </div>
      )}

      {recipes.length === 0 ? (
        <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
          <Heart className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {t('interactions.favorites.empty')}
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Browse recipes and click the heart icon to save your favorites here.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recipes.map(recipe => (
            <RecipeCard 
              key={recipe.id} 
              recipe={recipe} 
              navFrom="recipes"
              showActions={false}
            />
          ))}
        </div>
      )}
    </PageContainer>
  );
};

export default FavoritesPage;