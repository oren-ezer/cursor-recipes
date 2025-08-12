import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { apiClient, ApiError } from '../lib/api-client';
import type { Recipe } from '../lib/api-client';
import MainLayout from '../components/layout/MainLayout';
import PageContainer from '../components/layout/PageContainer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';

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
}

const RecipeEditPage: React.FC = () => {
  const { recipeId } = useParams<{ recipeId: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [recipe, setRecipe] = useState<Recipe | null>(null);
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
  });

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login', { state: { message: 'Please log in to edit a recipe' } });
    }
  }, [isAuthenticated, navigate]);

  // Fetch recipe data
  useEffect(() => {
    const fetchRecipe = async () => {
      if (!recipeId || !isAuthenticated) return;

      try {
        const data = await apiClient.getRecipe(parseInt(recipeId));
        setRecipe(data);
        
        // Populate form with existing data
        setFormData({
          title: data.title,
          description: data.description,
          ingredients: data.ingredients.length > 0 ? data.ingredients : [{ name: '', amount: '' }],
          instructions: data.instructions.length > 0 ? data.instructions : [''],
          preparation_time: data.preparation_time,
          cooking_time: data.cooking_time,
          servings: data.servings,
          difficulty_level: data.difficulty_level,
          is_public: data.is_public,
          image_url: data.image_url || '',
        });
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError('Failed to fetch recipe');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchRecipe();
  }, [recipeId, isAuthenticated]);

  const handleInputChange = (field: keyof RecipeFormData, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
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

    if (!validateForm() || !recipeId) {
      return;
    }

    setIsSaving(true);

    try {
      // Filter out empty ingredients and instructions
      const cleanIngredients = formData.ingredients.filter(ing => ing.name.trim() && ing.amount.trim());
      const cleanInstructions = formData.instructions.filter(inst => inst.trim());

      const recipeData = {
        ...formData,
        ingredients: cleanIngredients,
        instructions: cleanInstructions,
        image_url: formData.image_url || undefined,
      };

      await apiClient.updateRecipe(parseInt(recipeId), recipeData);
      
      navigate(`/recipes/${recipeId}`, {
        state: { message: 'Recipe updated successfully!' }
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to update recipe');
    } finally {
      setIsSaving(false);
    }
  };

  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  if (isLoading) {
    return (
      <MainLayout>
        <PageContainer>
          <div className="text-center">
            <p className="text-lg text-gray-600 dark:text-gray-300">Loading recipe...</p>
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
              onClick={() => navigate('/recipes/my')}
            >
              Back to My Recipes
            </Button>
          </div>
        </PageContainer>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <PageContainer
        title="Edit Recipe"
        description="Update your recipe details and share with the community."
      >
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Basic Information */}
          <Card>
            <CardHeader>
              <CardTitle>Basic Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="title">Recipe Title *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  placeholder="e.g., Classic Margherita Pizza"
                  required
                  disabled={isSaving}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="A brief description of your recipe..."
                  rows={3}
                  disabled={isSaving}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="preparation_time">Preparation Time (minutes) *</Label>
                  <Input
                    id="preparation_time"
                    type="number"
                    min="1"
                    value={formData.preparation_time}
                    onChange={(e) => handleInputChange('preparation_time', parseInt(e.target.value))}
                    required
                    disabled={isSaving}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cooking_time">Cooking Time (minutes) *</Label>
                  <Input
                    id="cooking_time"
                    type="number"
                    min="1"
                    value={formData.cooking_time}
                    onChange={(e) => handleInputChange('cooking_time', parseInt(e.target.value))}
                    required
                    disabled={isSaving}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="servings">Servings *</Label>
                  <Input
                    id="servings"
                    type="number"
                    min="1"
                    value={formData.servings}
                    onChange={(e) => handleInputChange('servings', parseInt(e.target.value))}
                    required
                    disabled={isSaving}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="difficulty">Difficulty Level</Label>
                  <Select
                    value={formData.difficulty_level}
                    onValueChange={(value) => handleInputChange('difficulty_level', value)}
                    disabled={isSaving}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="Easy">Easy</SelectItem>
                      <SelectItem value="Medium">Medium</SelectItem>
                      <SelectItem value="Hard">Hard</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="image_url">Image URL (optional)</Label>
                  <Input
                    id="image_url"
                    type="url"
                    value={formData.image_url}
                    onChange={(e) => handleInputChange('image_url', e.target.value)}
                    placeholder="https://example.com/image.jpg"
                    disabled={isSaving}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Ingredients */}
          <Card>
            <CardHeader>
              <CardTitle>Ingredients *</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {formData.ingredients.map((ingredient, index) => (
                <div key={index} className="flex gap-4 items-end">
                  <div className="flex-1 space-y-2">
                    <Label htmlFor={`ingredient-name-${index}`}>Ingredient Name</Label>
                    <Input
                      id={`ingredient-name-${index}`}
                      value={ingredient.name}
                      onChange={(e) => handleIngredientChange(index, 'name', e.target.value)}
                      placeholder="e.g., Flour"
                      required
                      disabled={isSaving}
                    />
                  </div>
                  <div className="flex-1 space-y-2">
                    <Label htmlFor={`ingredient-amount-${index}`}>Amount</Label>
                    <Input
                      id={`ingredient-amount-${index}`}
                      value={ingredient.amount}
                      onChange={(e) => handleIngredientChange(index, 'amount', e.target.value)}
                      placeholder="e.g., 2 cups"
                      required
                      disabled={isSaving}
                    />
                  </div>
                  {formData.ingredients.length > 1 && (
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      onClick={() => removeIngredient(index)}
                      disabled={isSaving}
                    >
                      Remove
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={addIngredient}
                disabled={isSaving}
              >
                Add Ingredient
              </Button>
            </CardContent>
          </Card>

          {/* Instructions */}
          <Card>
            <CardHeader>
              <CardTitle>Instructions *</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {formData.instructions.map((instruction, index) => (
                <div key={index} className="flex gap-4">
                  <div className="flex-1 space-y-2">
                    <Label htmlFor={`instruction-${index}`}>Step {index + 1}</Label>
                    <Textarea
                      id={`instruction-${index}`}
                      value={instruction}
                      onChange={(e) => handleInstructionChange(index, e.target.value)}
                      placeholder={`Step ${index + 1}...`}
                      rows={2}
                      required
                      disabled={isSaving}
                    />
                  </div>
                  {formData.instructions.length > 1 && (
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      onClick={() => removeInstruction(index)}
                      disabled={isSaving}
                      className="self-end"
                    >
                      Remove
                    </Button>
                  )}
                </div>
              ))}
              <Button
                type="button"
                variant="outline"
                onClick={addInstruction}
                disabled={isSaving}
              >
                Add Step
              </Button>
            </CardContent>
          </Card>

          {/* Visibility */}
          <Card>
            <CardHeader>
              <CardTitle>Visibility</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="is_public"
                  checked={formData.is_public}
                  onChange={(e) => handleInputChange('is_public', e.target.checked)}
                  disabled={isSaving}
                  className="rounded"
                />
                <Label htmlFor="is_public">Make this recipe public</Label>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                Public recipes can be viewed by anyone. Private recipes are only visible to you.
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
              onClick={() => navigate(`/recipes/${recipeId}`)}
              disabled={isSaving}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSaving}>
              {isSaving ? 'Updating Recipe...' : 'Update Recipe'}
            </Button>
          </div>
        </form>
      </PageContainer>
    </MainLayout>
  );
};

export default RecipeEditPage;
