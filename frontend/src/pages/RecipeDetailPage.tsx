import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiClient, ApiError } from '../lib/api-client';
import type { Recipe } from '../lib/api-client';
import MainLayout from '../components/layout/MainLayout';
import PageContainer from '../components/layout/PageContainer';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import RecipeCard from '../components/RecipeCard';

const RecipeDetailPage: React.FC = () => {
  const { recipeId } = useParams<{ recipeId: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecipe = async () => {
      if (!recipeId) {
        setError('Recipe ID is required');
        setIsLoading(false);
        return;
      }

      // Validate recipeId is a valid number
      const parsedId = parseInt(recipeId);
      if (isNaN(parsedId) || parsedId <= 0) {
        setError('Invalid recipe ID');
        setIsLoading(false);
        return;
      }

      try {
        const data = await apiClient.getRecipe(parsedId);
        setRecipe(data);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('Failed to fetch recipe');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecipe();
  }, [recipeId]);

  const handleEdit = () => {
    navigate(`/recipes/${recipeId}/edit`);
  };

  const handleDelete = async () => {
    if (!recipe || !window.confirm(`Are you sure you want to delete "${recipe.title}"?`)) {
      return;
    }

    try {
      await apiClient.deleteRecipe(recipe.id);
      navigate('/recipes/my', {
        state: { message: 'Recipe deleted successfully' }
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to delete recipe');
    }
  };

  const formatTime = (minutes: number): string => {
    if (minutes < 60) {
      return `${minutes} minutes`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours} hour${hours > 1 ? 's' : ''} ${remainingMinutes} minutes` : `${hours} hour${hours > 1 ? 's' : ''}`;
  };

  const getDifficultyColor = (difficulty: string): string => {
    switch (difficulty.toLowerCase()) {
      case 'easy':
        return 'text-green-600 dark:text-green-400';
      case 'medium':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'hard':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  if (isLoading) {
    return (
      <MainLayout>
        <PageContainer>
          <div className="text-center">
            <p className="text-lg text-gray-600 dark:text-gray-300">Loading recipe...</p>
          </div>
        </PageContainer>
      </MainLayout>
    );
  }

  if (error || !recipe) {
    return (
      <MainLayout>
        <PageContainer>
          <div className="text-center">
            <p className="text-lg text-red-600 dark:text-red-400">
              {error || 'Recipe not found'}
            </p>
            <Button 
              variant="outline" 
              className="mt-4"
              onClick={() => navigate('/recipes')}
            >
              Back to Recipes
            </Button>
          </div>
        </PageContainer>
      </MainLayout>
    );
  }

  const isOwner = isAuthenticated && recipe.user_id; // In a real app, you'd compare with current user ID

  return (
    <MainLayout>
      <PageContainer
        title={recipe.title}
        description={recipe.description}
      >
        <div className="space-y-6">
          {/* Recipe Card Preview */}
          <div className="max-w-md mx-auto">
            <RecipeCard
              recipe={recipe}
              variant="compact"
              showActions={false}
            />
          </div>

          {/* Action Buttons */}
          {isOwner && (
            <div className="flex justify-center gap-4">
              <Button onClick={handleEdit}>
                Edit Recipe
              </Button>
              <Button 
                variant="destructive" 
                onClick={handleDelete}
              >
                Delete Recipe
              </Button>
            </div>
          )}

          {/* Recipe Details */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recipe Information */}
            <Card>
              <CardHeader>
                <CardTitle>Recipe Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">Preparation Time:</span>
                    <p>{formatTime(recipe.preparation_time)}</p>
                  </div>
                  <div>
                    <span className="font-medium">Cooking Time:</span>
                    <p>{formatTime(recipe.cooking_time)}</p>
                  </div>
                  <div>
                    <span className="font-medium">Servings:</span>
                    <p>{recipe.servings} people</p>
                  </div>
                  <div>
                    <span className="font-medium">Difficulty:</span>
                    <p className={getDifficultyColor(recipe.difficulty_level)}>
                      {recipe.difficulty_level}
                    </p>
                  </div>
                </div>
                {recipe.image_url && (
                  <div>
                    <span className="font-medium">Image:</span>
                    <p className="text-blue-600 dark:text-blue-400">Available</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Tags */}
            {recipe.tags && recipe.tags.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Tags</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {recipe.tags.map((tag) => (
                      <span
                        key={tag.id}
                        className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                      >
                        {tag.name}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Ingredients */}
            <Card>
              <CardHeader>
                <CardTitle>Ingredients</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {recipe.ingredients.map((ingredient, index) => (
                    <li key={index} className="flex justify-between items-center">
                      <span className="font-medium">{ingredient.name}</span>
                      <span className="text-gray-600 dark:text-gray-400">
                        {ingredient.amount}
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>Instructions</CardTitle>
            </CardHeader>
            <CardContent>
              <ol className="space-y-4">
                {recipe.instructions.map((instruction, index) => (
                  <li key={index} className="flex gap-4">
                    <span className="flex-shrink-0 w-8 h-8 bg-primary text-primary-foreground rounded-full flex items-center justify-center text-sm font-medium">
                      {index + 1}
                    </span>
                    <p className="flex-1">{instruction}</p>
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>

          {/* Navigation */}
          <div className="flex justify-center gap-4">
            <Button 
              variant="outline" 
              onClick={() => navigate('/recipes')}
            >
              Back to Recipes
            </Button>
            {isAuthenticated && (
              <Button 
                variant="outline" 
                onClick={() => navigate('/recipes/my')}
              >
                My Recipes
              </Button>
            )}
          </div>
        </div>
      </PageContainer>
    </MainLayout>
  );
};

export default RecipeDetailPage;
