import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
// import { useAuth } from '../contexts/AuthContext'; // Not used yet
import { apiClient, ApiError } from '../lib/api-client';
import type { Recipe, Tag } from '../lib/api-client';
import PageContainer from '../components/layout/PageContainer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import RecipeCard from '../components/RecipeCard';
import ConfirmationModal from '../components/ui/confirmation-modal';
import { useRecipeDeletion } from '../hooks/useRecipeDeletion';
import TagSelector from '../components/ui/tag-selector';
import { useLanguage } from '../contexts/LanguageContext';

const MyRecipesPage: React.FC = () => {
  // const { isAuthenticated } = useAuth(); // Not used yet
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<Tag[]>([]);

  // Use the consistent deletion hook
  const {
    isDeleting,
    showDeleteModal,
    recipeToDelete,
    handleDeleteClick,
    handleDeleteConfirm,
    handleDeleteCancel
  } = useRecipeDeletion({
    onSuccess: (deletedRecipe) => {
      // Update local state by removing the deleted recipe
      setRecipes(recipes.filter(r => r.id !== deletedRecipe.id));
    },
    onError: (errorMessage) => {
      setError(errorMessage);
    }
  });

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
  }, [t]);

  const handleLoadTags = async () => {
    return await apiClient.getAllTags();
  };

  const handleDeleteRecipe = handleDeleteClick;

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
      <PageContainer>
        <div className="text-center">
          <p className="text-lg text-gray-600 dark:text-gray-300">{t('my_recipes.loading')}</p>
        </div>
      </PageContainer>
    );
  }

  return (
    <PageContainer
      title={t('my_recipes.title')}
      description={t('my_recipes.description')}
    >
      <div className="space-y-6">
        <div className="flex flex-col md:flex-row gap-4 justify-between items-start">
          <div className="flex flex-col sm:flex-row gap-4 flex-1 w-full">
            <div className="w-full sm:w-72">
            <Input
              type="search"
              placeholder={t('my_recipes.search.placeholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full"
            />
          </div>
            <div className="flex-1 min-w-[200px]">
              <TagSelector
                value={selectedTags}
                onChange={setSelectedTags}
                placeholder={t('recipe.filter.tags')}
                onLoadTags={handleLoadTags}
              />
            </div>
          </div>
          <Button onClick={() => navigate('/recipes/new')} className="shrink-0">
            {t('recipe.create.button')}
          </Button>
        </div>

        {error ? (
          <div className="text-center py-8">
            <p className="text-lg text-red-600 dark:text-red-400">{error}</p>
          </div>
        ) : filteredRecipes.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-lg text-gray-600 dark:text-gray-300">
              {searchQuery || selectedTags.length > 0
                ? t('recipe.list.no_matches')
                : t('my_recipes.empty')}
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
      
      {/* Confirmation Modal */}
      <ConfirmationModal
        isOpen={showDeleteModal}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title={t('recipe.detail.delete_confirm_title')}
        message={t('recipe.detail.delete_confirm_message').replace('{title}', recipeToDelete?.title || '')}
        confirmText={t('recipe.detail.delete_button')}
        cancelText={t('modal.cancel')}
        variant="destructive"
        isLoading={isDeleting}
      />
    </PageContainer>
  );
};

export default MyRecipesPage; 