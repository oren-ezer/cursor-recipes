import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiClient, ApiError } from '../lib/api-client';
import type { Recipe, Tag } from '../lib/api-client';
import MainLayout from '../components/layout/MainLayout';
import PageContainer from '../components/layout/PageContainer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import RecipeCard from '../components/RecipeCard';
import TagSelector from '../components/ui/tag-selector';

const RecipeListPage: React.FC = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<Tag[]>([]);

  useEffect(() => {
    const fetchRecipes = async () => {
      try {
        const data = await apiClient.getRecipes();
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

    fetchRecipes();
  }, []);

  const handleLoadTags = async () => {
    return await apiClient.getAllTags();
  };

  const filteredRecipes = recipes.filter(recipe => {
    const matchesSearch = recipe.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      recipe.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    const matchesTags = selectedTags.length === 0 || selectedTags.every(tag => 
      recipe.tags && recipe.tags.some(recipeTag => recipeTag.id === tag.id)
    );

    return matchesSearch && matchesTags;
  });

  if (isLoading) {
    return (
      <MainLayout>
        <PageContainer>
          <div className="text-center">
            <p className="text-lg text-gray-600 dark:text-gray-300">Loading recipes...</p>
          </div>
        </PageContainer>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <PageContainer
        title="Recipes"
        description="Discover and explore delicious recipes from our community."
      >
        <div className="space-y-6">
          <div className="flex flex-col md:flex-row gap-4 justify-between items-start">
            <div className="flex flex-col sm:flex-row gap-4 flex-1 w-full">
              <div className="w-full sm:w-72">
                <Input
                  type="search"
                  placeholder="Search recipes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full"
                />
              </div>
              <div className="flex-1 min-w-[200px]">
                <TagSelector
                  value={selectedTags}
                  onChange={setSelectedTags}
                  placeholder="Filter by tags..."
                  onLoadTags={handleLoadTags}
                />
              </div>
            </div>
            {isAuthenticated && (
              <Button onClick={() => navigate('/recipes/new')} className="shrink-0">
                Create Recipe
              </Button>
            )}
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
                  : 'No recipes available yet. Be the first to create one!'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredRecipes.map((recipe) => (
                <RecipeCard
                  key={recipe.id}
                  recipe={recipe}
                  variant="default"
                />
              ))}
            </div>
          )}
        </div>
      </PageContainer>
    </MainLayout>
  );
};

export default RecipeListPage; 