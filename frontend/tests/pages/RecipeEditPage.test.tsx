import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';

// Mock all dependencies
vi.mock('../../src/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../../src/lib/api-client', () => ({
  apiClient: {
    getRecipe: vi.fn(),
    updateRecipe: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(message: string) {
      super(message);
      this.name = 'ApiError';
    }
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: vi.fn(),
    useNavigate: vi.fn(),
  };
});

// Import after mocks
import RecipeEditPage from '../../src/pages/RecipeEditPage';
import { useAuth } from '../../src/contexts/AuthContext';
import { apiClient } from '../../src/lib/api-client';
import { useParams, useNavigate } from 'react-router-dom';

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

// Helper function to create mock auth values
const createMockAuth = (isAuthenticated: boolean, user: any = null) => ({
  isAuthenticated,
  user,
  token: isAuthenticated ? 'mock-token' : null,
  login: vi.fn(),
  logout: vi.fn(),
  isLoading: false,
});

const mockRecipe = {
  id: 123,
  title: 'Test Recipe',
  description: 'A delicious test recipe',
  preparation_time: 30,
  cooking_time: 45,
  servings: 4,
  difficulty_level: 'Medium',
  ingredients: [
    { name: 'Ingredient 1', amount: '2 cups' },
    { name: 'Ingredient 2', amount: '1 tbsp' },
  ],
  instructions: [
    'Step 1: Do something',
    'Step 2: Do something else',
  ],
  image_url: 'https://example.com/image.jpg',
  user_id: '1',
  is_public: true,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
};

const mockUpdatedRecipe = {
  ...mockRecipe,
  title: 'Updated Recipe',
  description: 'An updated test recipe',
};

describe('RecipeEditPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    vi.mocked(useAuth).mockReturnValue(createMockAuth(true, { id: 1, email: 'test@example.com' }));
    vi.mocked(useParams).mockReturnValue({ recipeId: '123' });
    vi.mocked(useNavigate).mockReturnValue(vi.fn());
    vi.mocked(apiClient.getRecipe).mockResolvedValue(mockRecipe);
    vi.mocked(apiClient.updateRecipe).mockResolvedValue(mockUpdatedRecipe);
  });

  describe('Authentication', () => {
    it('should redirect to login when user is not authenticated', () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      vi.mocked(useAuth).mockReturnValue(createMockAuth(false));
      
      renderWithRouter(<RecipeEditPage />);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login', {
        state: { message: 'Please log in to edit a recipe' }
      });
    });

    it('should render form when user is authenticated', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
        expect(screen.getByText('Update your recipe details and share with the community.')).toBeInTheDocument();
      });
    });
  });

  describe('Data Loading', () => {
    it('should show loading state initially', () => {
      vi.mocked(apiClient.getRecipe).mockImplementation(() => new Promise(() => {})); // Never resolves
      
      renderWithRouter(<RecipeEditPage />);
      
      expect(screen.getByText('Loading recipe...')).toBeInTheDocument();
    });

    it('should fetch recipe data on mount', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.getRecipe)).toHaveBeenCalledWith(123);
      });
    });

    it('should populate form with recipe data', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        expect(screen.getByDisplayValue('Test Recipe')).toBeInTheDocument();
        expect(screen.getByDisplayValue('A delicious test recipe')).toBeInTheDocument();
        expect(screen.getByDisplayValue('30')).toBeInTheDocument(); // preparation time
        expect(screen.getByDisplayValue('45')).toBeInTheDocument(); // cooking time
        expect(screen.getByDisplayValue('4')).toBeInTheDocument(); // servings
      });
    });

    it('should show error when recipe fetch fails', async () => {
      vi.mocked(apiClient.getRecipe).mockRejectedValue(new Error('Failed to fetch recipe'));
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to fetch recipe')).toBeInTheDocument();
      });
    });

    it('should show error when recipe ID is missing', async () => {
      vi.mocked(useParams).mockReturnValue({ recipeId: undefined });
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Recipe ID is required')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /back to my recipes/i })).toBeInTheDocument();
      });
    });
  });

  describe('Form Rendering', () => {
    it('should render all form sections when data is loaded', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Basic Information')).toBeInTheDocument();
        expect(screen.getByText('Ingredients *')).toBeInTheDocument();
        expect(screen.getByText('Instructions *')).toBeInTheDocument();
        expect(screen.getByText('Visibility')).toBeInTheDocument();
      });
    });

    it('should render all form fields with pre-populated data', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        // Basic Information
        expect(screen.getByDisplayValue('Test Recipe')).toBeInTheDocument();
        expect(screen.getByDisplayValue('A delicious test recipe')).toBeInTheDocument();
        
        // Cooking Details
        expect(screen.getByDisplayValue('30')).toBeInTheDocument(); // preparation time
        expect(screen.getByDisplayValue('45')).toBeInTheDocument(); // cooking time
        expect(screen.getByDisplayValue('4')).toBeInTheDocument(); // servings
        expect(screen.getByText(/difficulty level/i)).toBeInTheDocument();
        
        // Additional Settings
        expect(screen.getByDisplayValue('https://example.com/image.jpg')).toBeInTheDocument();
        expect(screen.getByLabelText(/make this recipe public/i)).toBeChecked();
      });
    });

    it('should render submit button', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /update recipe/i })).toBeInTheDocument();
      });
    });
  });

  describe('Form Interactions', () => {
    it('should handle title input change', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const titleInput = screen.getByDisplayValue('Test Recipe');
        fireEvent.change(titleInput, { target: { value: 'Updated Recipe Title' } });
        
        expect(titleInput).toHaveValue('Updated Recipe Title');
      });
    });

    it('should handle description input change', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const descriptionInput = screen.getByDisplayValue('A delicious test recipe');
        fireEvent.change(descriptionInput, { target: { value: 'Updated description' } });
        
        expect(descriptionInput).toHaveValue('Updated description');
      });
    });

    it('should handle preparation time change', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const prepTimeInput = screen.getByDisplayValue('30');
        fireEvent.change(prepTimeInput, { target: { value: '45' } });
        
        expect(prepTimeInput).toHaveValue(45);
      });
    });

    it('should handle cooking time change', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const cookTimeInput = screen.getByDisplayValue('45');
        fireEvent.change(cookTimeInput, { target: { value: '60' } });
        
        expect(cookTimeInput).toHaveValue(60);
      });
    });

    it('should handle servings change', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const servingsInput = screen.getByDisplayValue('4');
        fireEvent.change(servingsInput, { target: { value: '6' } });
        
        expect(servingsInput).toHaveValue(6);
      });
    });

    it('should handle image URL change', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const imageUrlInput = screen.getByDisplayValue('https://example.com/image.jpg');
        fireEvent.change(imageUrlInput, { target: { value: 'https://example.com/new-image.jpg' } });
        
        expect(imageUrlInput).toHaveValue('https://example.com/new-image.jpg');
      });
    });

    it('should handle public/private toggle', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const publicToggle = screen.getByLabelText(/make this recipe public/i);
        fireEvent.click(publicToggle);
        
        expect(publicToggle).not.toBeChecked();
      });
    });
  });

  describe('Ingredients Management', () => {
    it('should display existing ingredients', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        expect(screen.getByDisplayValue('Ingredient 1')).toBeInTheDocument();
        expect(screen.getByDisplayValue('2 cups')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Ingredient 2')).toBeInTheDocument();
        expect(screen.getByDisplayValue('1 tbsp')).toBeInTheDocument();
      });
    });

    it('should add new ingredient', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      // First wait for the component to load and render the form
      await waitFor(() => {
        expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
      });
      
      // Then wait for the ingredients section to be rendered
      await waitFor(() => {
        expect(screen.getByText('Ingredients *')).toBeInTheDocument();
      });
      
      // Now try to find and click the add button
      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add ingredient/i });
        expect(addButton).toBeInTheDocument();
        fireEvent.click(addButton);
      });
      
      // Check that a new ingredient row was added
      await waitFor(() => {
        const nameInputs = screen.getAllByPlaceholderText(/e\.g\., Flour/i);
        expect(nameInputs.length).toBe(3); // 2 existing + 1 added
      });
    });

    it('should remove ingredient when more than one exists', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      // First wait for the component to load and render the form
      await waitFor(() => {
        expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
      });
      
      // Then wait for the ingredients section to be rendered
      await waitFor(() => {
        expect(screen.getByText('Ingredients *')).toBeInTheDocument();
      });
      
      // First add an ingredient
      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add ingredient/i });
        expect(addButton).toBeInTheDocument();
        fireEvent.click(addButton);
      });
      
      // Verify we now have 3 ingredients
      await waitFor(() => {
        const nameInputs = screen.getAllByPlaceholderText(/e\.g\., Flour/i);
        expect(nameInputs.length).toBe(3);
      });
      
      // Then remove one
      await waitFor(() => {
        const removeButtons = screen.getAllByRole('button', { name: /remove/i });
        expect(removeButtons.length).toBeGreaterThan(0);
        fireEvent.click(removeButtons[0]);
      });
      
      // Should be back to 2 ingredients (original)
      await waitFor(() => {
        const nameInputs = screen.getAllByPlaceholderText(/e\.g\., Flour/i);
        expect(nameInputs.length).toBe(2);
      });
    });

    it('should handle ingredient name change', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      // First wait for the component to load and render the form
      await waitFor(() => {
        expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
      });
      
      // Then wait for the ingredients section to be rendered
      await waitFor(() => {
        expect(screen.getByText('Ingredients *')).toBeInTheDocument();
      });
      
      await waitFor(() => {
        const nameInputs = screen.getAllByPlaceholderText(/e\.g\., Flour/i);
        expect(nameInputs.length).toBeGreaterThan(0);
        fireEvent.change(nameInputs[0], { target: { value: 'Updated Flour' } });
        
        expect(nameInputs[0]).toHaveValue('Updated Flour');
      });
    });

    it('should handle ingredient amount change', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      // First wait for the component to load and render the form
      await waitFor(() => {
        expect(screen.getByText('Edit Recipe')).toBeInTheDocument();
      });
      
      // Then wait for the ingredients section to be rendered
      await waitFor(() => {
        expect(screen.getByText('Ingredients *')).toBeInTheDocument();
      });
      
      await waitFor(() => {
        const amountInputs = screen.getAllByPlaceholderText(/e\.g\., 2 cups/i);
        expect(amountInputs.length).toBeGreaterThan(0);
        fireEvent.change(amountInputs[0], { target: { value: '3 cups' } });
        
        expect(amountInputs[0]).toHaveValue('3 cups');
      });
    });
  });

  describe('Instructions Management', () => {
    it('should display existing instructions', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        expect(screen.getByDisplayValue('Step 1: Do something')).toBeInTheDocument();
        expect(screen.getByDisplayValue('Step 2: Do something else')).toBeInTheDocument();
      });
    });

    it('should add new instruction', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const addButton = screen.getByRole('button', { name: /add step/i });
        fireEvent.click(addButton);
        
        // Should have 3 instruction rows (2 existing + 1 added)
        const instructionInputs = screen.getAllByPlaceholderText(/step \d+\.\.\./i);
        expect(instructionInputs.length).toBe(3);
      });
    });

    it('should remove instruction when more than one exists', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        // First add an instruction
        const addButton = screen.getByRole('button', { name: /add step/i });
        fireEvent.click(addButton);
        
        // Then remove it
        const removeButtons = screen.getAllByRole('button', { name: /remove/i });
        fireEvent.click(removeButtons[removeButtons.length - 1]); // Last remove button is for instruction
        
        // Should be back to 2 instructions (original)
        const instructionInputs = screen.getAllByPlaceholderText(/step \d+\.\.\./i);
        expect(instructionInputs.length).toBe(2);
      });
    });

    it('should handle instruction change', async () => {
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const instructionInputs = screen.getAllByPlaceholderText(/step \d+\.\.\./i);
        fireEvent.change(instructionInputs[0], { target: { value: 'Updated step 1' } });
        
        expect(instructionInputs[0]).toHaveValue('Updated step 1');
      });
    });
  });

  describe('Form Validation', () => {
    it('should show error when title is empty', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const titleInput = screen.getByDisplayValue('Test Recipe');
        fireEvent.change(titleInput, { target: { value: '' } });
        
        const form = document.querySelector('form');
        fireEvent.submit(form!);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Recipe title is required')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /back to my recipes/i })).toBeInTheDocument();
      });
    });

    it('should show error when ingredient is missing name or amount', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const nameInputs = screen.getAllByPlaceholderText(/e\.g\., Flour/i);
        fireEvent.change(nameInputs[0], { target: { value: '' } });
        
        const form = document.querySelector('form');
        fireEvent.submit(form!);
      });
      
      await waitFor(() => {
        expect(screen.getByText('All ingredients must have both name and amount')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /back to my recipes/i })).toBeInTheDocument();
      });
    });

    it('should show error when instruction is empty', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const instructionInputs = screen.getAllByPlaceholderText(/step \d+\.\.\./i);
        fireEvent.change(instructionInputs[0], { target: { value: '' } });
        
        const form = document.querySelector('form');
        fireEvent.submit(form!);
      });
      
      await waitFor(() => {
        expect(screen.getByText('All instructions must not be empty')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /back to my recipes/i })).toBeInTheDocument();
      });
    });

    it('should show error when preparation time is invalid', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const prepTimeInput = screen.getByDisplayValue('30');
        fireEvent.change(prepTimeInput, { target: { value: '0' } });
        
        const form = document.querySelector('form');
        fireEvent.submit(form!);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Preparation and cooking times must be greater than 0')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /back to my recipes/i })).toBeInTheDocument();
      });
    });

    it('should show error when servings is invalid', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const servingsInput = screen.getByDisplayValue('4');
        fireEvent.change(servingsInput, { target: { value: '0' } });
        
        const form = document.querySelector('form');
        fireEvent.submit(form!);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Servings must be greater than 0')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /back to my recipes/i })).toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('should submit form successfully with valid data', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const titleInput = screen.getByDisplayValue('Test Recipe');
        fireEvent.change(titleInput, { target: { value: 'Updated Recipe' } });
        
        const descriptionInput = screen.getByDisplayValue('A delicious test recipe');
        fireEvent.change(descriptionInput, { target: { value: 'Updated description' } });
        
        const submitButton = screen.getByRole('button', { name: /update recipe/i });
        fireEvent.click(submitButton);
      });
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.updateRecipe)).toHaveBeenCalledWith(123, {
          title: 'Updated Recipe',
          description: 'Updated description',
          ingredients: [
            { name: 'Ingredient 1', amount: '2 cups' },
            { name: 'Ingredient 2', amount: '1 tbsp' },
          ],
          instructions: [
            'Step 1: Do something',
            'Step 2: Do something else',
          ],
          preparation_time: 30,
          cooking_time: 45,
          servings: 4,
          difficulty_level: 'Medium',
          is_public: true,
          image_url: 'https://example.com/image.jpg',
        });
      });
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/recipes/123', {
          state: { message: 'Recipe updated successfully!' }
        });
      });
    });

    it('should handle API error during submission', async () => {
      vi.mocked(apiClient.updateRecipe).mockRejectedValue(new Error('API Error'));
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /update recipe/i });
        fireEvent.click(submitButton);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Failed to update recipe')).toBeInTheDocument();
      });
    });

    it('should handle ApiError during submission', async () => {
      vi.mocked(apiClient.updateRecipe).mockRejectedValue(new Error('Validation failed'));
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const submitButton = screen.getByRole('button', { name: /update recipe/i });
        fireEvent.click(submitButton);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Failed to update recipe')).toBeInTheDocument();
      });
    });

    // it('should disable form during submission', async () => {
    //   vi.mocked(apiClient.updateRecipe).mockImplementation(() => new Promise(() => {})); // Never resolves
      
    //   renderWithRouter(<RecipeEditPage />);
      
    //   await waitFor(() => {
    //     const submitButton = screen.getByRole('button', { name: /update recipe/i });
    //     fireEvent.click(submitButton);
    //   });
      
    //   await waitFor(() => {
    //     expect(screen.getByRole('button', { name: /update recipe/i })).toBeDisabled();
    //   });
    // });
  });

  describe('Form State Management', () => {
    it('should show error page when form validation fails', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        // Submit with invalid data to trigger error
        const titleInput = screen.getByDisplayValue('Test Recipe');
        fireEvent.change(titleInput, { target: { value: '' } });
        
        const form = document.querySelector('form');
        fireEvent.submit(form!);
      });
      
      await waitFor(() => {
        // Should show error page with error message
        expect(screen.getByText('Recipe title is required')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /back to my recipes/i })).toBeInTheDocument();
      });
    });

    it('should navigate back to my recipes when error page button is clicked', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        // Submit with invalid data to trigger error
        const titleInput = screen.getByDisplayValue('Test Recipe');
        fireEvent.change(titleInput, { target: { value: '' } });
        
        const form = document.querySelector('form');
        fireEvent.submit(form!);
      });
      
      await waitFor(() => {
        // Click the back button on error page
        const backButton = screen.getByRole('button', { name: /back to my recipes/i });
        fireEvent.click(backButton);
      });
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/recipes/my');
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle recipe with no ingredients', async () => {
      const recipeWithNoIngredients = {
        ...mockRecipe,
        ingredients: [],
      };
      vi.mocked(apiClient.getRecipe).mockResolvedValue(recipeWithNoIngredients);
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        // Should have one empty ingredient row
        const nameInputs = screen.getAllByPlaceholderText(/e\.g\., Flour/i);
        expect(nameInputs.length).toBe(1);
        expect(nameInputs[0]).toHaveValue('');
      });
    });

    it('should handle recipe with no instructions', async () => {
      const recipeWithNoInstructions = {
        ...mockRecipe,
        instructions: [],
      };
      vi.mocked(apiClient.getRecipe).mockResolvedValue(recipeWithNoInstructions);
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        // Should have one empty instruction row
        const instructionInputs = screen.getAllByPlaceholderText(/Step \d+\.\.\./i);
        expect(instructionInputs.length).toBe(1);
        expect(instructionInputs[0]).toHaveValue('');
      });
    });

    it('should handle recipe with no image URL', async () => {
      const recipeWithNoImage = {
        ...mockRecipe,
        image_url: undefined,
      };
      vi.mocked(apiClient.getRecipe).mockResolvedValue(recipeWithNoImage);
      
      renderWithRouter(<RecipeEditPage />);
      
      await waitFor(() => {
        const imageUrlInput = screen.getByLabelText(/image url/i);
        expect(imageUrlInput).toHaveValue('');
      });
    });
  });
});
