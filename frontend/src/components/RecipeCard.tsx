import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "./ui/card";
import type { Recipe } from '../lib/api-client';

export interface RecipeCardProps {
  recipe: Recipe;
  variant?: 'default' | 'my-recipes' | 'compact';
  showActions?: boolean;
  onEdit?: (recipe: Recipe) => void;
  onDelete?: (recipe: Recipe) => void;
  onView?: (recipe: Recipe) => void;
  onShare?: (recipe: Recipe) => void;
  onUnshare?: (recipe: Recipe) => void;
  className?: string;
}

const RecipeCard: React.FC<RecipeCardProps> = ({
  recipe,
  variant = 'default',
  showActions = true,
  onEdit,
  onDelete,
  onView,
  onShare,
  onUnshare,
  className = '',
}) => {
  const navigate = useNavigate();

  const handleView = () => {
    if (onView) {
      onView(recipe);
    } else {
      navigate(`/recipes/${recipe.id}`);
    }
  };

  const handleEdit = () => {
    if (onEdit) {
      onEdit(recipe);
    } else {
      navigate(`/recipes/${recipe.id}/edit`);
    }
  };

  const handleDelete = () => {
    if (onDelete) {
      onDelete(recipe);
    }
  };

  const handleShare = () => {
    if (onShare) {
      onShare(recipe);
    }
  };

  const handleUnshare = () => {
    if (onUnshare) {
      onUnshare(recipe);
    }
  };

  const formatTime = (minutes: number): string => {
    if (minutes < 60) {
      return `${minutes}m`;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`;
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

  const renderActions = () => {
    if (!showActions) return null;

    switch (variant) {
      case 'my-recipes':
        return (
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={handleView}
            >
              View
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={handleEdit}
            >
              Edit
            </Button>
            {onDelete && (
              <Button
                variant="destructive"
                size="sm"
                onClick={handleDelete}
              >
                Delete
              </Button>
            )}
          </div>
        );
      
      case 'compact':
        return (
          <Button
            variant="outline"
            size="sm"
            className="w-full"
            onClick={handleView}
          >
            View Recipe
          </Button>
        );
      
      default:
        return (
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex-1"
              onClick={handleView}
            >
              View Recipe
            </Button>
            {onShare && !recipe.is_public && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleShare}
              >
                Share
              </Button>
            )}
            {onUnshare && recipe.is_public && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleUnshare}
              >
                Unshare
              </Button>
            )}
          </div>
        );
    }
  };

  const renderContent = () => {
    if (variant === 'compact') {
      return (
        <CardContent className="p-4">
          <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-300">
            <span>{recipe.ingredients.length} ingredients</span>
            <span className={getDifficultyColor(recipe.difficulty_level)}>
              {recipe.difficulty_level}
            </span>
          </div>
        </CardContent>
      );
    }

    return (
      <CardContent className="p-4">
        <div className="space-y-2 text-sm text-gray-600 dark:text-gray-300">
          <div className="flex items-center justify-between">
            <span>{recipe.ingredients.length} ingredients</span>
            <span className={getDifficultyColor(recipe.difficulty_level)}>
              {recipe.difficulty_level}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span>Prep: {formatTime(recipe.preparation_time)}</span>
            <span>Cook: {formatTime(recipe.cooking_time)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Serves: {recipe.servings}</span>
            {recipe.image_url && (
              <span className="text-blue-600 dark:text-blue-400">Has image</span>
            )}
          </div>
        </div>
      </CardContent>
    );
  };

  return (
    <Card className={`hover:shadow-lg transition-shadow ${className}`}>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg line-clamp-2">{recipe.title}</CardTitle>
        <CardDescription className="line-clamp-2">
          {recipe.description}
        </CardDescription>
      </CardHeader>
      {renderContent()}
      <CardFooter className="pt-3">
        {renderActions()}
      </CardFooter>
    </Card>
  );
};

export default RecipeCard;
