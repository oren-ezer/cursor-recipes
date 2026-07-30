import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

import { apiClient, ApiError, type Tag } from '../lib/api-client';
import MainLayout from '../components/layout/MainLayout';
import PageContainer from '../components/layout/PageContainer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import TagSelector from '../components/ui/tag-selector';
import ImageUploader from '../components/ImageUploader';
import { Sparkles, X } from 'lucide-react';

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
  selectedTags: Tag[];
}

const RecipeCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const { t } = useLanguage();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fromImageFiles, setFromImageFiles] = useState<File[]>([]);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [isParsing, setIsParsing] = useState(false);
  const [parseSuccess, setParseSuccess] = useState(false);
  const [keepImages, setKeepImages] = useState(true);
  const [languageHint, setLanguageHint] = useState('');
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
    selectedTags: [],
  });

  const fromImagePreviews = useMemo(
    () => fromImageFiles.map((file) => ({ name: file.name, url: URL.createObjectURL(file) })),
    [fromImageFiles]
  );

  useEffect(() => {
    return () => {
      fromImagePreviews.forEach((p) => URL.revokeObjectURL(p.url));
    };
  }, [fromImagePreviews]);

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

  const handleAiTagSuggestion = async (): Promise<string[]> => {
    // Validate that we have the required data
    if (!formData.title.trim()) {
      throw new Error(t('recipe.form.ai_suggestion_no_title'));
    }
    
    const validIngredients = formData.ingredients.filter(ing => ing.name.trim());
    if (validIngredients.length === 0) {
      throw new Error(t('recipe.form.ai_suggestion_no_ingredients'));
    }

    try {
      const ingredientsList = validIngredients.map(ing => ing.name);
      const existingTagNames = formData.selectedTags.map(tag => tag.name);
      
      const response = await apiClient.suggestTags({
        recipe_title: formData.title,
        ingredients: ingredientsList,
        existing_tags: existingTagNames.length > 0 ? existingTagNames : undefined,
      });

      return response.suggested_tags;
    } catch (error) {
      console.error('Failed to get AI tag suggestions:', error);
      throw error;
    }
  };

  const handleParseImages = async () => {
    if (fromImageFiles.length === 0) return;
    setIsParsing(true);
    setError(null);
    setParseSuccess(false);
    try {
      const result = await apiClient.parseRecipeFromImages(
        fromImageFiles,
        languageHint || undefined,
      );
      setFormData((prev) => ({
        ...prev,
        title: result.title || prev.title,
        description: result.description || prev.description,
        ingredients: result.ingredients.length > 0
          ? result.ingredients.map((ing) => ({ name: ing.name, amount: ing.amount }))
          : prev.ingredients,
        instructions: result.instructions.length > 0
          ? result.instructions
          : prev.instructions,
        preparation_time: result.preparation_time || prev.preparation_time,
        cooking_time: result.cooking_time || prev.cooking_time,
        servings: result.servings || prev.servings,
        difficulty_level: result.difficulty_level || prev.difficulty_level,
      }));
      setParseSuccess(true);
    } catch {
      setError(t('recipe.from_image.error'));
    } finally {
      setIsParsing(false);
    }
  };

  const removeFromImageFile = (index: number) => {
    setFromImageFiles((prev) => prev.filter((_, i) => i !== index));
    setParseSuccess(false);
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

    if (formData.selectedTags.length < 3) {
      setError(t('recipe.form.tags_min_required'));
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
        tag_ids: formData.selectedTags.map(tag => tag.id),
      };

      const createdRecipe = await apiClient.createRecipe(recipeData);

      const imagesToAttach = [
        ...pendingFiles,
        ...(keepImages ? fromImageFiles : []),
      ];
      if (imagesToAttach.length > 0) {
        try {
          await apiClient.uploadImages(imagesToAttach, createdRecipe.id);
        } catch {
          // Recipe created; image upload failed — user can add images on edit
        }
      }

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
          {/* Create from Image (AI) */}
          <Card className="border-purple-200 dark:border-purple-800 bg-gradient-to-br from-purple-50/80 via-white to-indigo-50/80 dark:from-purple-950/40 dark:via-background dark:to-indigo-950/40 shadow-sm overflow-hidden">
            <CardHeader className="space-y-3">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="inline-flex items-center gap-1 rounded-full bg-gradient-to-r from-purple-500 to-indigo-600 px-2.5 py-0.5 text-xs font-semibold text-white shadow-sm">
                  <Sparkles className="h-3 w-3" />
                  {t('recipe.from_image.ai_badge')}
                </span>
              </div>
              <CardTitle className="flex items-center gap-2 text-purple-900 dark:text-purple-100">
                <Sparkles className="h-5 w-5 text-purple-500 dark:text-purple-300" />
                {t('recipe.from_image.section_title')}
              </CardTitle>
              <p className="text-sm text-purple-800/70 dark:text-purple-200/70">
                {t('recipe.from_image.upload_prompt')}
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              {fromImagePreviews.length > 0 && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                  {fromImagePreviews.map((preview, index) => (
                    <div key={`${preview.name}-${index}`} className="relative group rounded-md overflow-hidden border border-purple-200 dark:border-purple-800">
                      <img
                        src={preview.url}
                        alt={preview.name}
                        className="w-full h-28 object-cover"
                      />
                      <button
                        type="button"
                        onClick={() => removeFromImageFile(index)}
                        disabled={isLoading || isParsing}
                        className="absolute top-1 right-1 rtl:right-auto rtl:left-1 rounded-full bg-destructive/80 text-destructive-foreground p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                        aria-label={t('image_upload.remove')}
                      >
                        <X className="h-3 w-3" />
                      </button>
                      <p className="text-xs truncate px-2 py-1 bg-white/80 dark:bg-black/40">{preview.name}</p>
                    </div>
                  ))}
                </div>
              )}

              <div className="rounded-lg border border-dashed border-purple-300 dark:border-purple-700 bg-white/60 dark:bg-purple-950/20 p-1">
                <ImageUploader
                  deferUpload
                  disabled={isLoading || isParsing}
                  onFilesReady={(files) => {
                    setFromImageFiles((prev) => [...prev, ...files]);
                    setParseSuccess(false);
                  }}
                />
              </div>

              {fromImageFiles.length > 0 && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="language_hint">{t('recipe.from_image.language_hint')}</Label>
                    <Input
                      id="language_hint"
                      value={languageHint}
                      onChange={(e) => setLanguageHint(e.target.value)}
                      placeholder={t('recipe.from_image.language_placeholder')}
                      maxLength={50}
                      disabled={isLoading || isParsing}
                    />
                  </div>

                  <Button
                    type="button"
                    onClick={handleParseImages}
                    disabled={isLoading || isParsing || fromImageFiles.length === 0}
                    className="w-full bg-gradient-to-r from-purple-500 to-indigo-600 text-white hover:from-purple-600 hover:to-indigo-700 shadow-sm"
                  >
                    {isParsing ? (
                      <span className="flex items-center justify-center gap-2">
                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                        {t('recipe.from_image.parsing')}
                      </span>
                    ) : (
                      <span className="flex items-center justify-center gap-2">
                        <Sparkles className="h-4 w-4" />
                        {t('recipe.from_image.parse_button')}
                      </span>
                    )}
                  </Button>

                  {parseSuccess && (
                    <p className="text-sm text-green-600 dark:text-green-400 font-medium rounded-md bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 px-3 py-2">
                      {t('recipe.from_image.success')}
                    </p>
                  )}

                  <div className="flex items-center space-x-2">
                    <input
                      type="checkbox"
                      id="keep_images"
                      checked={keepImages}
                      onChange={(e) => setKeepImages(e.target.checked)}
                      disabled={isLoading}
                      className="rounded"
                    />
                    <Label htmlFor="keep_images">{t('recipe.from_image.keep_images')}</Label>
                  </div>
                </>
              )}

              {fromImageFiles.length === 0 && (
                <p className="text-sm text-purple-700/60 dark:text-purple-300/60 text-center">
                  {t('recipe.from_image.or_manual')}
                </p>
              )}
            </CardContent>
          </Card>

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
                  maxLength={200}
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
                  maxLength={5000}
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
                    max="4320"
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
                    max="4320"
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
                    max="100"
                    value={formData.servings}
                    onChange={(e) => handleInputChange('servings', parseInt(e.target.value))}
                    required
                    disabled={isLoading}
                  />
                </div>
              </div>

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
            </CardContent>
          </Card>

          {/* Tags */}
          <Card>
            <CardHeader>
              <CardTitle>{t('recipe.form.tags')} *</CardTitle>
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
                  showAiSuggestion={true}
                  onSuggestTags={handleAiTagSuggestion}
                />
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {t('recipe.form.tags_help_with_ai')}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Recipe Images (uploaded after create) */}
          <Card>
            <CardHeader>
              <CardTitle>{t('recipe.form.images')}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {pendingFiles.length > 0 && (
                <p className="text-sm text-muted-foreground">
                  {pendingFiles.length} {t('image_upload.add_files').toLowerCase()}
                </p>
              )}
              <ImageUploader
                deferUpload
                disabled={isLoading || isParsing}
                onFilesReady={(files) => {
                  setPendingFiles((prev) => [...prev, ...files]);
                }}
              />
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
                      maxLength={200}
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
                      maxLength={100}
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
                      maxLength={2000}
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
              onClick={() => navigate('/my-recipes')}
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
