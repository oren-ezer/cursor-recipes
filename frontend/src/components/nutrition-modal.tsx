import React from 'react';
import { X } from 'lucide-react';
import { useLanguage } from '../contexts/LanguageContext';

interface NutritionData {
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  fiber_g?: number;
  sodium_mg?: number;
}

interface NutritionModalProps {
  isOpen: boolean;
  onClose: () => void;
  nutrition: NutritionData | null;
  isLoading: boolean;
  error: string | null;
  recipeName: string;
}

const NutritionModal: React.FC<NutritionModalProps> = ({
  isOpen,
  onClose,
  nutrition,
  isLoading,
  error,
  recipeName
}) => {
  const { t } = useLanguage();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="relative w-full max-w-md rounded-lg bg-white dark:bg-gray-800 shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-700 p-4">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            {t('nutrition.modal_title')}
          </h2>
          <button
            onClick={onClose}
            className="rounded-full p-1 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            aria-label={t('common.close')}
          >
            <X className="h-5 w-5 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Recipe Name */}
          <p className="mb-4 text-sm text-gray-600 dark:text-gray-400">
            {t('nutrition.recipe_label')}: <span className="font-medium text-gray-900 dark:text-gray-100">{recipeName}</span>
          </p>

          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-8">
              <div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" />
              <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">
                {t('nutrition.calculating')}
              </p>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <div className="rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 p-4 text-sm text-red-800 dark:text-red-200">
              {error}
            </div>
          )}

          {/* Nutrition Data */}
          {nutrition && !isLoading && !error && (
            <div className="space-y-3">
              <div className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                {t('nutrition.per_serving')}
              </div>

              {/* Nutrition Table */}
              <div className="space-y-2">
                {/* Calories */}
                {nutrition.calories !== undefined && (
                  <NutritionRow
                    label={t('nutrition.calories')}
                    value={Math.round(nutrition.calories)}
                    unit={t('nutrition.kcal')}
                    highlight={true}
                  />
                )}

                {/* Macronutrients */}
                {nutrition.protein_g !== undefined && (
                  <NutritionRow
                    label={t('nutrition.protein')}
                    value={nutrition.protein_g.toFixed(1)}
                    unit="g"
                  />
                )}

                {nutrition.carbs_g !== undefined && (
                  <NutritionRow
                    label={t('nutrition.carbs')}
                    value={nutrition.carbs_g.toFixed(1)}
                    unit="g"
                  />
                )}

                {nutrition.fat_g !== undefined && (
                  <NutritionRow
                    label={t('nutrition.fat')}
                    value={nutrition.fat_g.toFixed(1)}
                    unit="g"
                  />
                )}

                {nutrition.fiber_g !== undefined && (
                  <NutritionRow
                    label={t('nutrition.fiber')}
                    value={nutrition.fiber_g.toFixed(1)}
                    unit="g"
                  />
                )}

                {nutrition.sodium_mg !== undefined && (
                  <NutritionRow
                    label={t('nutrition.sodium')}
                    value={Math.round(nutrition.sodium_mg)}
                    unit="mg"
                  />
                )}
              </div>

              {/* Disclaimer */}
              <div className="mt-4 rounded-md bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-3 text-xs text-blue-800 dark:text-blue-200">
                ℹ️ {t('nutrition.disclaimer')}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end border-t border-gray-200 dark:border-gray-700 p-4">
          <button
            onClick={onClose}
            className="rounded-md bg-gray-200 dark:bg-gray-700 px-4 py-2 text-sm font-medium text-gray-900 dark:text-gray-100 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            {t('common.close')}
          </button>
        </div>
      </div>
    </div>
  );
};

// Helper component for nutrition rows
interface NutritionRowProps {
  label: string;
  value: number | string;
  unit: string;
  highlight?: boolean;
}

const NutritionRow: React.FC<NutritionRowProps> = ({ label, value, unit, highlight = false }) => {
  return (
    <div className={`flex items-center justify-between py-2 px-3 rounded-md ${
      highlight 
        ? 'bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800' 
        : 'bg-gray-50 dark:bg-gray-700/50'
    }`}>
      <span className={`text-sm ${
        highlight 
          ? 'font-semibold text-indigo-900 dark:text-indigo-100' 
          : 'font-medium text-gray-700 dark:text-gray-300'
      }`}>
        {label}
      </span>
      <span className={`text-sm ${
        highlight 
          ? 'font-bold text-indigo-900 dark:text-indigo-100' 
          : 'font-semibold text-gray-900 dark:text-gray-100'
      }`}>
        {value} {unit}
      </span>
    </div>
  );
};

export default NutritionModal;

