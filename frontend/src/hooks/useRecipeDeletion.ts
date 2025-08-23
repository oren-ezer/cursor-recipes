import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiClient, ApiError } from '../lib/api-client';
import type { Recipe } from '../lib/api-client';

interface UseRecipeDeletionOptions {
  onSuccess?: (deletedRecipe: Recipe) => void;
  onError?: (error: string) => void;
  onNavigate?: () => void;
  navigateAfterDelete?: boolean;
  navigateTo?: string;
  showSuccessModal?: boolean;
}

export const useRecipeDeletion = (options: UseRecipeDeletionOptions = {}) => {
  const navigate = useNavigate();
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [recipeToDelete, setRecipeToDelete] = useState<Recipe | null>(null);
  const [deletedRecipe, setDeletedRecipe] = useState<Recipe | null>(null);

  const {
    onSuccess,
    onError,
    onNavigate,
    navigateAfterDelete = false,
    navigateTo = '/recipes/my',
    showSuccessModal: enableSuccessModal = false
  } = options;

  const handleDeleteClick = (recipe: Recipe) => {
    setRecipeToDelete(recipe);
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (!recipeToDelete) return;

    setIsDeleting(true);
    try {
      await apiClient.deleteRecipe(recipeToDelete.id);
      
      // Call success callback if provided
      if (onSuccess) {
        onSuccess(recipeToDelete);
      }

      // Store the deleted recipe for success modal
      setDeletedRecipe(recipeToDelete);
      
      // Reset delete modal state
      setShowDeleteModal(false);
      setRecipeToDelete(null);

      // Show success modal if enabled, otherwise navigate immediately
      if (enableSuccessModal) {
        setShowSuccessModal(true);
      } else if (navigateAfterDelete) {
        // Navigate with replace to prevent back button issues
        navigate(navigateTo, {
          state: { message: 'Recipe deleted successfully' },
          replace: true
        });
      }
    } catch (err) {
      const errorMessage = err instanceof ApiError ? err.message : 'Failed to delete recipe';
      
      // Call error callback if provided
      if (onError) {
        onError(errorMessage);
      }
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteModal(false);
    setRecipeToDelete(null);
  };

  const handleSuccessModalClose = () => {
    setShowSuccessModal(false);
    setDeletedRecipe(null);
    
          // Navigate after user closes the success modal
      if (navigateAfterDelete) {
        // Call navigation callback if provided
        if (onNavigate) {
          onNavigate();
        }
        
        // Use React Router navigate with replace
        navigate(navigateTo, { replace: true });
      }
  };

  return {
    isDeleting,
    showDeleteModal,
    showSuccessModal,
    recipeToDelete,
    deletedRecipe,
    handleDeleteClick,
    handleDeleteConfirm,
    handleDeleteCancel,
    handleSuccessModalClose
  };
};
