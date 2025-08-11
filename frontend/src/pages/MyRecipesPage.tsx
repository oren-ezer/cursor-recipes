import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiClient, ApiError } from '../lib/api-client';
import type { Recipe } from '../lib/api-client';
import PageContainer from '../components/layout/PageContainer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import RecipeCard from '../components/RecipeCard';

const MyRecipesPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const fetchMyRecipes = async () => {
      try {
        const data = await apiClient.getMyRecipes();
        setRecipes(data);
      } catch (err) {
        // If the backend is not implemented yet, just show an empty list
        if (err instanceof ApiError && err.message.includes('Failed to fetch')) {
          setRecipes([]);
        } else {
          setError(err instanceof ApiError ? err.message : 'Failed to fetch recipes');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchMyRecipes();
  }, []);

  const handleDeleteRecipe = async (recipe: Recipe) => {
    if (window.confirm(`Are you sure you want to delete "${recipe.title}"?`)) {
      try {
        await apiClient.deleteRecipe(recipe.id);
        setRecipes(recipes.filter(r => r.id !== recipe.id));
      } catch (err) {
        setError(err instanceof ApiError ? err.message : 'Failed to delete recipe');
      }
    }
  };

  const filteredRecipes = recipes.filter(recipe =>
    recipe.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    recipe.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (isLoading) {
    return (
      <PageContainer>
        <div className="text-center">
          <p className="text-lg text-gray-600 dark:text-gray-300">Loading your recipes...</p>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title="My Recipes"
      description="Manage and organize your personal recipe collection."
    >
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <div className="flex-1 max-w-sm">
            <Input
              type="search"
              placeholder="Search your recipes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full"
            />
          </div>
          <Button onClick={() => navigate('/recipes/new')}>
            Create Recipe
          </Button>
        </div>

        {error ? (
          <div className="text-center py-8">
            <p className="text-lg text-red-600 dark:text-red-400">{error}</p>
          </div>
        ) : filteredRecipes.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-lg text-gray-600 dark:text-gray-300">
              {searchQuery
                ? 'No recipes match your search.'
                : 'You haven\'t created any recipes yet. Start by creating your first recipe!'}
            </p>
          </div>
                  ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredRecipes.map((recipe) => (
                <RecipeCard
                  key={recipe.id}
                  recipe={recipe}
                  variant="my-recipes"
                  onDelete={handleDeleteRecipe}
                />
              ))}
            </div>
          )}
      </div>
    </PageContainer>
  );
};

export default MyRecipesPage; 