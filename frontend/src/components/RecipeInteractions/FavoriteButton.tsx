import React, { useState } from 'react';
import { Heart } from 'lucide-react';
import { Button } from '../ui/button';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiClient } from '../../lib/api-client';
import { useAuth } from '../../contexts/AuthContext';

interface FavoriteButtonProps {
  recipeId: number;
  initialIsFavorited?: boolean;
  initialCount?: number;
  onToggle?: (isFavorited: boolean, newCount: number) => void;
  className?: string;
}

export const FavoriteButton: React.FC<FavoriteButtonProps> = ({
  recipeId,
  initialIsFavorited = false,
  initialCount = 0,
  onToggle,
  className = '',
}) => {
  const [isFavorited, setIsFavorited] = useState(initialIsFavorited);
  const [count, setCount] = useState(initialCount);
  const [isLoading, setIsLoading] = useState(false);
  const { t } = useLanguage();
  const { isAuthenticated } = useAuth();

  const handleToggle = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!isAuthenticated || isLoading) return;

    setIsLoading(true);
    try {
      const response = await apiClient.toggleFavorite(recipeId);
      const newIsFavorited = response.status === 'added';
      const newCount = newIsFavorited ? count + 1 : Math.max(0, count - 1);
      
      setIsFavorited(newIsFavorited);
      setCount(newCount);
      
      if (onToggle) {
        onToggle(newIsFavorited, newCount);
      }
    } catch (error) {
      console.error('Failed to toggle favorite:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      className={`flex items-center gap-2 ${className}`}
      onClick={handleToggle}
      disabled={isLoading || !isAuthenticated}
      title={isFavorited ? t('interactions.favorites.remove') : t('interactions.favorites.add')}
    >
      <Heart 
        className={`w-5 h-5 transition-colors ${
          isFavorited ? 'fill-red-500 text-red-500' : 'text-gray-500 hover:text-red-500'
        }`}
      />
      {count > 0 && <span className="text-sm font-medium">{count}</span>}
    </Button>
  );
};