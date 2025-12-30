import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { apiClient, ApiError } from '../lib/api-client';
import type { Recipe } from '../lib/api-client';
import MainLayout from '../components/layout/MainLayout';
import PageContainer from '../components/layout/PageContainer';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import RecipeCard from '../components/RecipeCard';
import ConfirmationModal from '../components/ui/confirmation-modal';
import { useRecipeDeletion } from '../hooks/useRecipeDeletion';

const RecipeDetailPage: React.FC = () => {
  const { recipeId } = useParams<{ recipeId: string }>();
  const navigate = useNavigate();
  const { t } = useLanguage();
  
  const { isAuthenticated, user } = useAuth();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasNavigated, setHasNavigated] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);

  // Use the consistent deletion hook
  const {
    isDeleting,
    showDeleteModal,
    showSuccessModal,
    recipeToDelete,
    deletedRecipe,
    handleDeleteClick,
    handleDeleteConfirm,
    handleDeleteCancel,
    handleSuccessModalClose
  } = useRecipeDeletion({
    onSuccess: () => {
      // Clear any existing errors when deletion succeeds
      setError(null);
    },
    onError: (errorMessage) => {
      setError(errorMessage);
    },
    onNavigate: () => {
      setHasNavigated(true); // Mark that we're navigating
    },
    navigateAfterDelete: true,
    navigateTo: '/recipes/my',
    showSuccessModal: true // Enable success modal
  });

  useEffect(() => {
    // Don't fetch if we're in the process of deleting
    if (isDeleting) {
      return;
    }

    // Don't fetch if we don't have a valid recipeId
    if (!recipeId) {
      return;
    }

    // Don't fetch if recipeId is invalid (likely due to navigation)
    const parsedId = parseInt(recipeId);
    if (isNaN(parsedId) || parsedId <= 0) {
      // Reset loading state since we're not fetching
      setIsLoading(false);
      return;
    }

    // Don't fetch if we have an error (to prevent repeated failed requests)
    if (error) {
      return;
    }

    // Don't fetch if the delete modal is open (user is in the process of deleting)
    if (showDeleteModal) {
      return;
    }

    // Don't fetch if the success modal is open (deletion completed, waiting for user action)
    if (showSuccessModal) {
      return;
    }

    // Don't fetch if we've already navigated away
    if (hasNavigated) {
      return;
    }

    let isCancelled = false;

    const fetchRecipe = async () => {
      // recipeId validation is already done at the useEffect level
      const parsedId = parseInt(recipeId!); // We know recipeId is valid here

      try {
        const data = await apiClient.getRecipe(parsedId);
        if (!isCancelled) {
          setRecipe(data);
          setError(null); // Clear any previous errors
        }
      } catch (err) {
        if (!isCancelled) {
          if (err instanceof ApiError) {
            setError(err.message);
          } else {
            setError(t('recipe.list.error'));
          }
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    };

    // Only set loading to true if we're actually going to fetch
    setIsLoading(true);
    fetchRecipe();

    // Cleanup function to cancel the fetch if component unmounts or dependencies change
    return () => {
      console.log('Cleaning up useEffect - cancelling fetch');
      isCancelled = true;
    };
  }, [recipeId, isDeleting, error, showDeleteModal, showSuccessModal, hasNavigated, t]);

  // Reset navigation flag when recipeId changes (navigating to different recipe)
  useEffect(() => {
    setHasNavigated(false);
  }, [recipeId]);

      // Cleanup effect when component unmounts
    useEffect(() => {
      return () => {
        setIsLoading(false);
        setError(null);
        setHasNavigated(false);
      };
    }, []);

  const handleEdit = () => {
    navigate(`/recipes/${recipeId}/edit`);
  };

  const handleExportPdf = async () => {
    if (!recipe) return;
    
    setIsExporting(true);
    setError(null);
    setExportSuccess(null);
    
    try {
      const blob = await apiClient.exportRecipeToPdf(recipe.id);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${recipe.title.replace(/\s+/g, '_')}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setExportSuccess(t('recipe.detail.export_success'));
      setTimeout(() => setExportSuccess(null), 3000);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(t('recipe.detail.export_error'));
      }
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportJson = async () => {
    if (!recipe) return;
    
    setIsExporting(true);
    setError(null);
    setExportSuccess(null);
    
    try {
      const data = await apiClient.exportRecipeToJson(recipe.id);
      
      // Create download link
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${recipe.title.replace(/\s+/g, '_')}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      setExportSuccess(t('recipe.detail.export_success'));
      setTimeout(() => setExportSuccess(null), 3000);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(t('recipe.detail.export_error'));
      }
    } finally {
      setIsExporting(false);
    }
  };

  const handleDeleteButtonClick = () => {
    if (recipe) {
      handleDeleteClick(recipe);
    }
  };

  const formatTime = (minutes: number): string => {
    if (minutes < 60) {
      return `${minutes} ${t('time.minutes')}`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    const hourKey = hours > 1 ? 'time.hours' : 'time.hour';
    return remainingMinutes > 0 ? `${hours} ${t(hourKey)} ${remainingMinutes} ${t('time.minutes')}` : `${hours} ${t(hourKey)}`;
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
            <p className="text-lg text-gray-600 dark:text-gray-300">{t('recipe.list.loading')}</p>
          </div>
        </PageContainer>
      </MainLayout>
    );
  }

  if (isDeleting) {
    return (
      <MainLayout>
        <PageContainer>
          <div className="text-center">
            <p className="text-lg text-gray-600 dark:text-gray-300">{t('recipe.detail.deleting')}</p>
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
              {t('recipe.detail.back')}
            </Button>
          </div>
        </PageContainer>
      </MainLayout>
    );
  }

  const isOwner = isAuthenticated && user && recipe.user_id && String(user.id) === String(recipe.user_id);

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

          {/* Export Success Message */}
          {exportSuccess && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-200 px-4 py-3 rounded text-center">
              {exportSuccess}
            </div>
          )}

          {/* Export Buttons - Available to all authenticated users */}
          {isAuthenticated && (
            <div className="flex justify-center gap-4">
              <Button 
                onClick={handleExportPdf}
                disabled={isExporting}
                variant="outline"
              >
                {isExporting ? t('recipe.detail.exporting') : t('recipe.detail.export_pdf')}
              </Button>
              {user?.is_superuser && (
                <Button 
                  onClick={handleExportJson}
                  disabled={isExporting}
                  variant="outline"
                >
                  {isExporting ? t('recipe.detail.exporting') : t('recipe.detail.export_json')}
                </Button>
              )}
            </div>
          )}

          {/* Action Buttons - Owner only */}
          {isOwner && (
            <div className="flex justify-center gap-4">
              <Button onClick={handleEdit}>
                {t('recipe.card.edit')}
              </Button>
              <Button 
                variant="destructive" 
                onClick={handleDeleteButtonClick}
              >
                {t('recipe.card.delete')}
              </Button>
            </div>
          )}

          {/* Recipe Details */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recipe Information */}
            <Card>
              <CardHeader>
                <CardTitle>{t('recipe.detail.info')}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium">{t('recipe.form.prep_time')}:</span>
                    <p>{formatTime(recipe.preparation_time)}</p>
                  </div>
                  <div>
                    <span className="font-medium">{t('recipe.form.cook_time')}:</span>
                    <p>{formatTime(recipe.cooking_time)}</p>
                  </div>
                  <div>
                    <span className="font-medium">{t('recipe.form.servings')}:</span>
                    <p>{recipe.servings} people</p>
                  </div>
                  <div>
                    <span className="font-medium">{t('recipe.form.difficulty')}:</span>
                    <p className={getDifficultyColor(recipe.difficulty_level)}>
                      {recipe.difficulty_level}
                    </p>
                  </div>
                </div>
                {recipe.image_url && (
                  <div>
                    <span className="font-medium">{t('recipe.detail.image')}:</span>
                    <p className="text-blue-600 dark:text-blue-400">{t('recipe.detail.available')}</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Tags */}
            {recipe.tags && recipe.tags.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>{t('recipe.form.tags')}</CardTitle>
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
                <CardTitle>{t('recipe.form.ingredients')}</CardTitle>
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
              <CardTitle>{t('recipe.form.instructions')}</CardTitle>
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
              {t('recipe.detail.back')}
            </Button>
            {isAuthenticated && (
              <Button 
                variant="outline" 
                onClick={() => navigate('/recipes/my')}
              >
                {t('recipe.detail.back_my')}
              </Button>
            )}
          </div>
        </div>
      </PageContainer>
      
      {/* Delete Confirmation Modal */}
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

      {/* Success Modal */}
      <ConfirmationModal
        isOpen={showSuccessModal}
        onClose={handleSuccessModalClose}
        onConfirm={handleSuccessModalClose}
        title={t('recipe.detail.deleted_title')}
        message={t('recipe.detail.deleted_message').replace('{title}', deletedRecipe?.title || '')}
        confirmText={t('recipe.detail.continue')}
        cancelText={t('modal.cancel')}
        variant="default"
        isLoading={false}
      />
    </MainLayout>
  );
};

export default RecipeDetailPage;
