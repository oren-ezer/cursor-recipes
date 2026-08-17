import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { apiClient, ApiError } from '../lib/api-client';
import type { Recipe, ImageInfo } from '../lib/api-client';
import MainLayout from '../components/layout/MainLayout';
import PageContainer from '../components/layout/PageContainer';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import ConfirmationModal from '../components/ui/confirmation-modal';
import { useRecipeDeletion } from '../hooks/useRecipeDeletion';
import NutritionModal from '../components/nutrition-modal';
import ImageThumbnailGrid from '../components/ImageThumbnailGrid';
import { Sparkles, Languages, FileText, Layout, X } from 'lucide-react';

import { FavoriteButton } from '../components/RecipeInteractions/FavoriteButton';
import { RatingStars } from '../components/RecipeInteractions/RatingStars';
import { CommentSection } from '../components/RecipeInteractions/CommentSection';

const RecipeDetailPage: React.FC = () => {
  const { recipeId } = useParams<{ recipeId: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, language } = useLanguage();
  
  const { isAuthenticated, user } = useAuth();
  const fromMyRecipes = (location.state as { from?: string } | null)?.from === 'my-recipes';
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hasNavigated, setHasNavigated] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState<string | null>(null);
  const [recipeImages, setRecipeImages] = useState<ImageInfo[]>([]);

  // Nutrition state
  const [showNutritionModal, setShowNutritionModal] = useState(false);
  const [nutritionData, setNutritionData] = useState<any>(null);
  const [isCalculatingNutrition, setIsCalculatingNutrition] = useState(false);
  const [nutritionError, setNutritionError] = useState<string | null>(null);

  const [showExportLangModal, setShowExportLangModal] = useState(false);
  const [detectedLanguage, setDetectedLanguage] = useState<'he' | 'en'>('en');

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
    navigateTo: '/my-recipes',
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
          setError(null);
          apiClient.getRecipeImages(parsedId).then((res) => {
            if (!isCancelled) setRecipeImages(res.images);
          }).catch(() => {});
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
    navigate(`/recipes/${recipeId}/edit`, { state: location.state });
  };

  const isRtlText = (text: string | null | undefined): boolean => {
    if (!text) return false;
    return /[\u0590-\u05FF]/.test(text);
  };

  const detectRecipeLanguage = (recipe: Recipe): string => {
    const texts = [
      recipe.title,
      recipe.description,
      recipe.difficulty_level,
      ...(recipe.ingredients?.map(i => i.name) || []),
      ...(recipe.ingredients?.map(i => i.amount) || []),
      ...(recipe.instructions || [])
    ];
    return texts.some(isRtlText) ? 'he' : 'en';
  };

  const handleExportPdfClick = () => {
    if (!recipe) return;
    
    const recipeLang = detectRecipeLanguage(recipe);
    if (recipeLang !== language) {
      setDetectedLanguage(recipeLang as 'he' | 'en');
      setShowExportLangModal(true);
    } else {
      handleExportPdf(recipeLang);
    }
  };

  const handleExportPdf = async (lang: string) => {
    if (!recipe) return;
    
    setShowExportLangModal(false);
    setIsExporting(true);
    setError(null);
    setExportSuccess(null);
    
    try {
      const blob = await apiClient.exportRecipeToPdf(recipe.id, lang);
      
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

  const handleCalculateNutrition = async () => {
    if (!recipe) return;
    
    setShowNutritionModal(true);
    setIsCalculatingNutrition(true);
    setNutritionError(null);
    setNutritionData(null);
    
    try {
      // Prepare ingredients data
      const ingredients = recipe.ingredients.map(ing => ({
        name: ing.name,
        amount: ing.amount
      }));
      
      const nutrition = await apiClient.calculateNutrition(ingredients, recipe.servings);
      setNutritionData(nutrition);
    } catch (err) {
      if (err instanceof ApiError) {
        setNutritionError(err.message);
      } else {
        setNutritionError(t('nutrition.error'));
      }
    } finally {
      setIsCalculatingNutrition(false);
    }
  };

  const handleCloseNutritionModal = () => {
    setShowNutritionModal(false);
    setNutritionData(null);
    setNutritionError(null);
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
              onClick={() => navigate(fromMyRecipes ? '/my-recipes' : '/recipes')}
            >
              {fromMyRecipes ? t('recipe.detail.back_my') : t('recipe.detail.back')}
            </Button>
          </div>
        </PageContainer>
      </MainLayout>
    );
  }

  const isOwner = isAuthenticated && user && recipe.user_id && (
    String(user.uuid) === String(recipe.user_id) ||
    String(user.id) === String(recipe.user_id) ||
    Boolean(user.is_superuser)
  );

  return (
    <MainLayout>
      <PageContainer
        title={recipe.title}
        description={recipe.description}
      >
        <div className="space-y-6">
          {/* Interaction Header */}
          <div className="flex flex-col md:flex-row justify-between items-center bg-white dark:bg-gray-800 p-4 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700">
            <RatingStars 
              recipeId={recipe.id}
              initialAverage={recipe.interaction_meta?.average_rating}
              initialCount={recipe.interaction_meta?.ratings_count}
              initialUserRating={recipe.interaction_meta?.user_rating}
              readOnly={false}
              size="lg"
            />
            <FavoriteButton 
              recipeId={recipe.id}
              initialIsFavorited={recipe.interaction_meta?.is_favorited}
              initialCount={recipe.interaction_meta?.favorites_count}
              className="mt-4 md:mt-0"
            />
          </div>

          {/* Export Success Message */}
          {exportSuccess && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-200 px-4 py-3 rounded text-center">
              {exportSuccess}
            </div>
          )}

          {/* Export and Nutrition Buttons - Available to all authenticated users */}
          {isAuthenticated && (
            <div className="flex justify-center gap-4 flex-wrap">
              <Button 
                onClick={handleCalculateNutrition}
                disabled={isCalculatingNutrition}
                className="bg-gradient-to-r from-purple-500 to-indigo-600 text-white hover:from-purple-600 hover:to-indigo-700 shadow-sm"
              >
                {isCalculatingNutrition ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                    {t('nutrition.calculating')}
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    {t('nutrition.calculate')}
                  </span>
                )}
              </Button>
              <Button 
                onClick={handleExportPdfClick}
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
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-sm">
                  <div className="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg flex flex-col items-center justify-center text-center">
                    <span className="font-medium text-gray-500 dark:text-gray-400">{t('recipe.form.prep_time')}</span>
                    <p className="text-base font-semibold mt-1">{formatTime(recipe.preparation_time)}</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg flex flex-col items-center justify-center text-center">
                    <span className="font-medium text-gray-500 dark:text-gray-400">{t('recipe.form.cook_time')}</span>
                    <p className="text-base font-semibold mt-1">{formatTime(recipe.cooking_time)}</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg flex flex-col items-center justify-center text-center">
                    <span className="font-medium text-gray-500 dark:text-gray-400">{t('recipe.form.servings')}</span>
                    <p className="text-base font-semibold mt-1">{recipe.servings}</p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg flex flex-col items-center justify-center text-center">
                    <span className="font-medium text-gray-500 dark:text-gray-400">{t('recipe.form.difficulty')}</span>
                    <p className={`text-base font-semibold mt-1 ${getDifficultyColor(recipe.difficulty_level)}`}>
                      {recipe.difficulty_level}
                    </p>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-800/50 p-3 rounded-lg flex flex-col items-center justify-center text-center sm:col-span-2">
                    <span className="font-medium text-gray-500 dark:text-gray-400">{t('recipe.form.origin')}</span>
                    <p className="text-base font-semibold text-gray-700 dark:text-gray-300 mt-1">
                      {recipe.origin || '-'}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Tags — always shown to keep the 4-quarter layout */}
            <Card>
              <CardHeader>
                <CardTitle>{t('recipe.form.tags')}</CardTitle>
              </CardHeader>
              <CardContent>
                {recipe.tags && recipe.tags.length > 0 ? (
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
                ) : null}
              </CardContent>
            </Card>

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

            {/* Images — always shown to keep the 4-quarter layout */}
            <Card>
              <CardHeader>
                <CardTitle>{t('recipe.detail.image')}</CardTitle>
              </CardHeader>
              <CardContent>
                {recipeImages.length > 0 ? (
                  <ImageThumbnailGrid images={recipeImages} />
                ) : recipe.image_url ? (
                  <ImageThumbnailGrid
                    images={[{
                      image_id: 'legacy',
                      serving_url: recipe.image_url,
                      filename: recipe.title,
                      size_bytes: 0,
                      is_primary: true,
                    }]}
                  />
                ) : null}
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

          {/* Comments Section */}
          <CommentSection recipeId={recipe.id} />

          {/* Navigation */}
          <div className="flex justify-center gap-4">
            <Button 
              variant="outline" 
              onClick={() => navigate(fromMyRecipes ? '/my-recipes' : '/recipes')}
            >
              {fromMyRecipes ? t('recipe.detail.back_my') : t('recipe.detail.back')}
            </Button>
            {isAuthenticated && !fromMyRecipes && (
              <Button 
                variant="outline" 
                onClick={() => navigate('/my-recipes')}
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

      {/* Nutrition Modal */}
      <NutritionModal
        isOpen={showNutritionModal}
        onClose={handleCloseNutritionModal}
        nutrition={nutritionData}
        isLoading={isCalculatingNutrition}
        error={nutritionError}
        recipeName={recipe?.title || ''}
      />

      {/* Export Language Conflict Modal */}
      {showExportLangModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="bg-white dark:bg-gray-900 border dark:border-gray-800 rounded-2xl shadow-2xl max-w-md w-full overflow-hidden animate-in zoom-in-95 duration-200">
            {/* Header */}
            <div className="p-6 border-b dark:border-gray-800 bg-gray-50/50 dark:bg-gray-800/50 flex justify-between items-start">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-full text-blue-600 dark:text-blue-400">
                  <Languages className="w-5 h-5" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                  {t('recipe.detail.export_lang_conflict_title')}
                </h3>
              </div>
              <button 
                onClick={() => setShowExportLangModal(false)}
                className="text-gray-400 hover:text-gray-500 dark:hover:text-gray-300 transition-colors rounded-full p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* Body */}
            <div className="p-6 space-y-6">
              <p className="text-gray-600 dark:text-gray-300 text-sm leading-relaxed">
                {t('recipe.detail.export_lang_conflict_desc')}
              </p>
              
              <div className="flex flex-col gap-3">
                <button
                  className="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-all text-left group"
                  onClick={() => handleExportPdf(detectedLanguage)}
                >
                  <div className="p-3 bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400 rounded-lg group-hover:bg-indigo-200 dark:group-hover:bg-indigo-900/50 transition-colors shrink-0">
                    <FileText className="w-6 h-6" />
                  </div>
                  <div className="ml-4 rtl:mr-4 rtl:ml-0 flex-1">
                    <div className="font-semibold text-gray-900 dark:text-white">
                      {t('recipe.detail.export_lang_recipe')}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                      {t(`recipe.detail.export_lang_${detectedLanguage}`)}
                    </div>
                  </div>
                </button>

                <button
                  className="flex items-center p-4 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-all text-left group"
                  onClick={() => handleExportPdf(language)}
                >
                  <div className="p-3 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 rounded-lg group-hover:bg-emerald-200 dark:group-hover:bg-emerald-900/50 transition-colors shrink-0">
                    <Layout className="w-6 h-6" />
                  </div>
                  <div className="ml-4 rtl:mr-4 rtl:ml-0 flex-1">
                    <div className="font-semibold text-gray-900 dark:text-white">
                      {t('recipe.detail.export_lang_ui')}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                      {t(`recipe.detail.export_lang_${language}`)}
                    </div>
                  </div>
                </button>
              </div>
              
              <div className="pt-2 flex justify-end">
                <Button
                  variant="ghost"
                  onClick={() => setShowExportLangModal(false)}
                >
                  {t('modal.cancel')}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </MainLayout>
  );
};

export default RecipeDetailPage;
