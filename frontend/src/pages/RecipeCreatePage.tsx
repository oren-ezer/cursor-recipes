import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';

import { apiClient, ApiError, type Tag, type ImageInfo } from '../lib/api-client';
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
import ImageThumbnailGrid from '../components/ImageThumbnailGrid';

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
  const [uploadedImages, setUploadedImages] = useState<ImageInfo[]>([]);
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
    if (uploadedImages.length === 0) return;
    setIsParsing(true);
    setError(null);
    setParseSuccess(false);
    try {
      const imageIds = uploadedImages.map((img) => img.image_id);
      const result = await apiClient.parseRecipeFromImages(
        imageIds,
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

      const primaryImageUrl = keepImages && uploadedImages.length > 0
        ? uploadedImages[0].serving_url
        : (formData.image_url || undefined);

      const recipeData = {
        ...formData,
        ingredients: cleanIngredients,
        instructions: cleanInstructions,
        image_url: primaryImageUrl,
        tag_ids: formData.selectedTags.map(tag => tag.id),
      };

      const createdRecipe = await apiClient.createRecipe(recipeData);

      if (keepImages && uploadedImages.length > 0) {
        try {
          await apiClient.associateImagesWithRecipe(
            uploadedImages.map((img) => img.image_id),
            createdRecipe.id,
          );
        } catch {
          // Non-critical: recipe is created, images just won't be linked
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
          {/* Create from Image */}
          <Card>
            <CardHeader>
              <CardTitle>{t('recipe.from_image.section_title')}</CardTitle>
              <p className="text-sm text-muted-foreground">
                {t('recipe.from_image.upload_prompt')}
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
              {uploadedImages.length > 0 && (
                <ImageThumbnailGrid images={uploadedImages} />
              )}

              <ImageUploader
                disabled={isLoading || isParsing}
                onUploadComplete={(images: ImageInfo[]) => {
                  setUploadedImages((prev) => [...prev, ...images]);
                  setParseSuccess(false);
                }}
              />

              {uploadedImages.length > 0 && (
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
                    disabled={isLoading || isParsing || uploadedImages.length === 0}
                    className="w-full"
                  >
                    {isParsing ? t('recipe.from_image.parsing') : t('recipe.from_image.parse_button')}
                  </Button>

                  {parseSuccess && (
                    <p className="text-sm text-green-600 dark:text-green-400 font-medium">
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

              {uploadedImages.length === 0 && (
                <p className="text-sm text-muted-foreground text-center">
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
                  showAiSuggestion={true}
                  onSuggestTags={handleAiTagSuggestion}
                />
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {t('recipe.form.tags_help_with_ai')}
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
