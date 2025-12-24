import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

import { apiClient, ApiError, type Tag } from '../lib/api-client';
// import type { Recipe } from '../lib/api-client'; // Not used yet
import MainLayout from '../components/layout/MainLayout';
import PageContainer from '../components/layout/PageContainer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import TagSelector from '../components/ui/tag-selector';

interface Ingredient {
  name: string;
  amount: string;
}

interface RecipeFormData {
  title: string;
  description: string;
  ingredients: Ingredient[];
  instructions: string[];
  preparation_time: number;
  cooking_time: number;
  servings: number;
  difficulty_level: string;
  is_public: boolean;
  image_url: string;
  selectedTags: Tag[];
}

const RecipeCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<RecipeFormData>({
    title: '',
    description: '',
    ingredients: [{ name: '', amount: '' }],
    instructions: [''],
    preparation_time: 30,
    cooking_time: 30,
    servings: 4,
    difficulty_level: 'Easy',
    is_public: true,
    image_url: '',
    selectedTags: [],
  });

  // Redirect if not authenticated
  React.useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { state: { message: t('recipe.form.login_required') } });
    }
  }, [isAuthenticated, navigate, t]);

  const handleInputChange = (field: keyof RecipeFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleTagsChange = (tags: Tag[]) => {
    setFormData(prev => ({
      ...prev,
      selectedTags: tags
    }));
  };

  const loadTagsWithLogging = async () => {
    console.log('loadTagsWithLogging called');
    try {
      const tags = await apiClient.getAllTags();
      console.log('Tags loaded successfully:', tags);
      return tags;
    } catch (error) {
      console.error('Error loading tags:', error);
      throw error;
    }
  };

  const handleIngredientChange = (index: number, field: 'name' | 'amount', value: string) => {
    const newIngredients = [...formData.ingredients];
    newIngredients[index] = { ...newIngredients[index], [field]: value };
    setFormData(prev => ({ ...prev, ingredients: newIngredients }));
  };

  const addIngredient = () => {
    setFormData(prev => ({
      ...prev,
      ingredients: [...prev.ingredients, { name: '', amount: '' }]
    }));
  };

  const removeIngredient = (index: number) => {
    if (formData.ingredients.length > 1) {
      const newIngredients = formData.ingredients.filter((_, i) => i !== index);
      setFormData(prev => ({ ...prev, ingredients: newIngredients }));
    }
  };

  const handleInstructionChange = (index: number, value: string) => {
    const newInstructions = [...formData.instructions];
    newInstructions[index] = value;
    setFormData(prev => ({ ...prev, instructions: newInstructions }));
  };

  const addInstruction = () => {
    setFormData(prev => ({
      ...prev,
      instructions: [...prev.instructions, '']
    }));
  };

  const removeInstruction = (index: number) => {
    if (formData.instructions.length > 1) {
      const newInstructions = formData.instructions.filter((_, i) => i !== index);
      setFormData(prev => ({ ...prev, instructions: newInstructions }));
    }
  };

  const validateForm = (): boolean => {
    if (!formData.title.trim()) {
      setError('Recipe title is required');
      return false;
    }

    if (formData.ingredients.some(ing => !ing.name.trim() || !ing.amount.trim())) {
      setError('All ingredients must have both name and amount');
      return false;
    }

    if (formData.instructions.some(inst => !inst.trim())) {
      setError('All instructions must not be empty');
      return false;
    }

    if (formData.preparation_time <= 0 || formData.cooking_time <= 0) {
      setError('Preparation and cooking times must be greater than 0');
      return false;
    }

    if (formData.servings <= 0) {
      setError('Servings must be greater than 0');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateForm()) {
      return;
    }

    setIsLoading(true);

    try {
      // Filter out empty ingredients and instructions
      const cleanIngredients = formData.ingredients.filter(ing => ing.name.trim() && ing.amount.trim());
      const cleanInstructions = formData.instructions.filter(inst => inst.trim());

      const recipeData = {
        ...formData,
        ingredients: cleanIngredients,
        instructions: cleanInstructions,
        image_url: formData.image_url || undefined,
        tag_ids: formData.selectedTags.map(tag => tag.id),
      };

      const createdRecipe = await apiClient.createRecipe(recipeData);
      
      navigate(`/recipes/${createdRecipe.id}`, {
        state: { message: 'Recipe created successfully!' }
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create recipe');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  return (
    <MainLayout>
      <PageContainer
        title={t('recipe.create.title')}
        description={t('recipe.create.description')}
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>{t('recipe.form.basic_info')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">{t('recipe.form.title')} *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  placeholder={t('recipe.form.title_placeholder')}
                  required
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">{t('recipe.form.description')}</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder={t('recipe.form.description_placeholder')}
                  rows={3}
                  disabled={isLoading}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="preparation_time">{t('recipe.form.prep_time')} *</Label>
                  <Input
                    id="preparation_time"
                    type="number"
                    min="1"
                    value={formData.preparation_time}
                    onChange={(e) => handleInputChange('preparation_time', parseInt(e.target.value))}
                    required
                    disabled={isLoading}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cooking_time">{t('recipe.form.cook_time')} *</Label>
                  <Input
                    id="cooking_time"
                    type="number"
                    min="1"
                    value={formData.cooking_time}
                    onChange={(e) => handleInputChange('cooking_time', parseInt(e.target.value))}
                    required
                    disabled={isLoading}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="servings">{t('recipe.form.servings')} *</Label>
                  <Input
                    id="servings"
                    type="number"
                    min="1"
                    value={formData.servings}
                    onChange={(e) => handleInputChange('servings', parseInt(e.target.value))}
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="difficulty">{t('recipe.form.difficulty')}</Label>
                  <Select
                    value={formData.difficulty_level}
                    onValueChange={(value) => handleInputChange('difficulty_level', value)}
                    disabled={isLoading}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Easy">{t('difficulty.easy')}</SelectItem>
                      <SelectItem value="Medium">{t('difficulty.medium')}</SelectItem>
                      <SelectItem value="Hard">{t('difficulty.hard')}</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="image_url">{t('recipe.form.image_url')}</Label>
                  <Input
                    id="image_url"
                    type="url"
                    value={formData.image_url}
                    onChange={(e) => handleInputChange('image_url', e.target.value)}
                    placeholder="https://example.com/image.jpg"
                    disabled={isLoading}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Tags */}
          <Card>
            <CardHeader>
              <CardTitle>{t('recipe.form.tags')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <Label>{t('recipe.form.recipe_tags')}</Label>
                <TagSelector
                  value={formData.selectedTags}
                  onChange={handleTagsChange}
                  placeholder={t('recipe.form.tags_placeholder')}
                  disabled={isLoading}
                  onLoadTags={loadTagsWithLogging}
                  showSearch={true}
                  showCategories={true}
                />
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {t('recipe.form.tags_help')}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Ingredients */}
          <Card>
            <CardHeader>
              <CardTitle>{t('recipe.form.ingredients')} *</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {formData.ingredients.map((ingredient, index) => (
                <div key={index} className="flex gap-4 items-end">
                  <div className="flex-1 space-y-2">
                    <Label htmlFor={`ingredient-name-${index}`}>{t('recipe.form.ingredient_name')}</Label>
                    <Input
                      id={`ingredient-name-${index}`}
                      value={ingredient.name}
                      onChange={(e) => handleIngredientChange(index, 'name', e.target.value)}
                      placeholder={t('recipe.form.ingredient_placeholder')}
                      required
                      disabled={isLoading}
                    />
                  </div>
                  <div className="flex-1 space-y-2">
                    <Label htmlFor={`ingredient-amount-${index}`}>{t('recipe.form.amount')}</Label>
                    <Input
                      id={`ingredient-amount-${index}`}
                      value={ingredient.amount}
                      onChange={(e) => handleIngredientChange(index, 'amount', e.target.value)}
                      placeholder={t('recipe.form.amount_placeholder')}
                      required
                      disabled={isLoading}
                    />
                  </div>
                  {formData.ingredients.length > 1 && (
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      onClick={() => removeIngredient(index)}
                      disabled={isLoading}
                    >
                      {t('recipe.form.remove')}
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={addIngredient}
                disabled={isLoading}
              >
                {t('recipe.form.add_ingredient')}
              </Button>
            </CardContent>
          </Card>

          {/* Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>{t('recipe.form.instructions')} *</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {formData.instructions.map((instruction, index) => (
                <div key={index} className="flex gap-4">
                  <div className="flex-1 space-y-2">
                    <Label htmlFor={`instruction-${index}`}>{t('recipe.form.step')} {index + 1}</Label>
                    <Textarea
                      id={`instruction-${index}`}
                      value={instruction}
                      onChange={(e) => handleInstructionChange(index, e.target.value)}
                      placeholder={`${t('recipe.form.step')} ${index + 1}...`}
                      rows={2}
                      required
                      disabled={isLoading}
                    />
                  </div>
                  {formData.instructions.length > 1 && (
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      onClick={() => removeInstruction(index)}
                      disabled={isLoading}
                      className="self-end"
                    >
                      {t('recipe.form.remove')}
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={addInstruction}
                disabled={isLoading}
              >
                {t('recipe.form.add_step')}
              </Button>
            </CardContent>
          </Card>

          {/* Visibility */}
          <Card>
            <CardHeader>
              <CardTitle>{t('recipe.form.visibility')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="is_public"
                  checked={formData.is_public}
                  onChange={(e) => handleInputChange('is_public', e.target.checked)}
                  disabled={isLoading}
                  className="rounded"
                />
                <Label htmlFor="is_public">{t('recipe.form.make_public')}</Label>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                {t('recipe.form.public_help')}
              </p>
            </CardContent>
          </Card>

          {/* Error Display */}
          {error && (
            <div className="text-center">
              <p className="text-sm font-medium text-destructive">{error}</p>
            </div>
          )}

          {/* Form Actions */}
          <div className="flex justify-center gap-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => navigate('/recipes/my')}
              disabled={isLoading}
            >
              {t('recipe.form.cancel')}
            </Button>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? t('recipe.form.creating') : t('recipe.form.create')}
            </Button>
          </div>
        </form>
      </PageContainer>
    </MainLayout>
  );
};

export default RecipeCreatePage;
