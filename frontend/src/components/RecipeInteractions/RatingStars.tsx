import React, { useState } from 'react';
import { Star } from 'lucide-react';
import { useLanguage } from '../../contexts/LanguageContext';
import { apiClient } from '../../lib/api-client';
import { useAuth } from '../../contexts/AuthContext';

interface RatingStarsProps {
  recipeId: number;
  initialAverage?: number;
  initialCount?: number;
  initialUserRating?: number | null;
  readOnly?: boolean;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
}

export const RatingStars: React.FC<RatingStarsProps> = ({
  recipeId,
  initialAverage = 0,
  initialCount = 0,
  initialUserRating = null,
  readOnly = false,
  className = '',
  size = 'md',
  showDetails = true,
}) => {
  const [average, setAverage] = useState(initialAverage);
  const [count, setCount] = useState(initialCount);
  const [userRating, setUserRating] = useState<number | null>(initialUserRating);
  const [hoverRating, setHoverRating] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { t } = useLanguage();
  const { isAuthenticated } = useAuth();

  const handleRate = async (score: number) => {
    if (readOnly || !isAuthenticated || isLoading) return;

    setIsLoading(true);
    try {
      await apiClient.setRating(recipeId, score);
      
      // Calculate new average simply (in reality, backend should return updated avg/count)
      // We will just optimistically update the user rating
      if (userRating === null) {
        setCount(c => c + 1);
        setAverage(a => (a * count + score) / (count + 1));
      } else {
        setAverage(a => (a * count - userRating + score) / count);
      }
      setUserRating(score);
    } catch (error) {
      console.error('Failed to set rating:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const currentDisplayRating = hoverRating !== null ? hoverRating : (userRating || average);
  
  const starSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6'
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div 
        className="flex"
        onMouseLeave={() => !readOnly && setHoverRating(null)}
      >
        {[1, 2, 3, 4, 5].map((star) => {
          const isFilled = star <= Math.round(currentDisplayRating);
          return (
            <button
              key={star}
              type="button"
              disabled={readOnly || !isAuthenticated || isLoading}
              className={`${readOnly || !isAuthenticated ? 'cursor-default' : 'cursor-pointer hover:scale-110 transition-transform'}`}
              onMouseEnter={() => !readOnly && isAuthenticated && setHoverRating(star)}
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                handleRate(star);
              }}
              title={!readOnly ? t('interactions.ratings.rate_this') : undefined}
            >
              <Star
                className={`${starSizes[size]} ${
                  isFilled 
                    ? 'fill-yellow-400 text-yellow-400' 
                    : 'text-gray-300 dark:text-gray-600'
                }`}
              />
            </button>
          );
        })}
      </div>
      
      {showDetails && (
        <div className="text-sm text-gray-500 dark:text-gray-400 flex flex-col sm:flex-row gap-1 sm:gap-2">
          {count > 0 ? (
            <>
              <span className="font-medium">{average.toFixed(1)}</span>
              <span>{t('interactions.ratings.count').replace('{count}', count.toString())}</span>
            </>
          ) : (
            <span>-</span>
          )}
        </div>
      )}
    </div>
  );
};