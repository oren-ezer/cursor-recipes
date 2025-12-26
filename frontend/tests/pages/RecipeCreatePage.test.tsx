import React from 'react';
import { render, screen, fireEvent, waitFor } from '../setup/test-utils';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';

// Mock all dependencies
vi.mock('../../src/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
  AuthContext: {
    Provider: ({ children }: { children: React.ReactNode }) => children,
    Consumer: ({ children }: any) => children(vi.fn()),
  },
}));

vi.mock('../../src/lib/api-client', () => ({
  apiClient: {
    createRecipe: vi.fn(),
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
    useNavigate: vi.fn(),
  };
});

// Mock Select component with better structure
vi.mock('../../src/components/ui/select', () => ({
  Select: ({ children, value, onValueChange, disabled }: any) => (
    <div 
      data-testid="select" 
      data-value={value} 
      data-disabled={disabled}
      className="select-root"
      style={{ display: 'block', width: '100%' }}
    >
      {children}
    </div>
  ),
  SelectTrigger: ({ children, disabled, className }: any) => (
    <button 
      data-testid="select-trigger" 
      disabled={disabled}
      className={className}
      style={{ 
        display: 'flex', 
        width: '100%', 
        padding: '8px 12px',
        border: '1px solid #ccc',
        borderRadius: '4px',
        backgroundColor: 'white'
      }}
    >
      {children}
    </button>
  ),
  SelectValue: ({ placeholder, children }: any) => (
    <span 
      data-testid="select-value"
      style={{ display: 'block', width: '100%' }}
    >
      {children || placeholder}
    </span>
  ),
  SelectContent: ({ children, className }: any) => (
    <div 
      data-testid="select-content" 
      className={className}
      style={{ 
        display: 'block',
        position: 'relative',
        backgroundColor: 'white',
        border: '1px solid #ccc',
        borderRadius: '4px',
        padding: '4px 0'
      }}
    >
      {children}
    </div>
  ),
  SelectItem: ({ value, children, className }: any) => (
    <div 
      data-testid="select-item" 
      data-value={value}
      className={className}
      style={{ 
        display: 'block',
        padding: '8px 12px',
        cursor: 'pointer',
        borderBottom: '1px solid #eee'
      }}
    >
      {children}
    </div>
  ),
}));

// Import after mocks
import RecipeCreatePage from '../../src/pages/RecipeCreatePage';
import { useAuth } from '../../src/contexts/AuthContext';
import { apiClient } from '../../src/lib/api-client';
import { useNavigate } from 'react-router-dom';

const renderWithRouter = (component: React.ReactElement) => {
  return render(component);
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

const mockCreatedRecipe = {
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

describe('RecipeCreatePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    vi.mocked(useAuth).mockReturnValue(createMockAuth(true, { id: 1, email: 'test@example.com' }));
    vi.mocked(useNavigate).mockReturnValue(vi.fn());
    vi.mocked(apiClient.createRecipe).mockResolvedValue(mockCreatedRecipe);
  });

  describe('Component Rendering', () => {
    it('should render without crashing', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      expect(() => {
        renderWithRouter(<RecipeCreatePage />);
      }).not.toThrow();
      
      consoleSpy.mockRestore();
    });

    it('should render the main heading', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      renderWithRouter(<RecipeCreatePage />);
      expect(screen.getByText('Create New Recipe')).toBeInTheDocument();
      
      consoleSpy.mockRestore();
    });

    it('should not have console errors', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      renderWithRouter(<RecipeCreatePage />);
      
      expect(consoleSpy).not.toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('Authentication', () => {
    it('should redirect to login when user is not authenticated', () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      vi.mocked(useAuth).mockReturnValue(createMockAuth(false));
      
      renderWithRouter(<RecipeCreatePage />);
      
      expect(mockNavigate).toHaveBeenCalledWith('/login', {
        state: { message: 'Please log in to create a recipe' }
      });
    });

    it('should render form when user is authenticated', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      expect(screen.getByText('Create New Recipe')).toBeInTheDocument();
      expect(screen.getByText('Share your culinary masterpiece with the community.')).toBeInTheDocument();
    });
  });

  describe('Form Rendering', () => {
    it('should render all form sections', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      expect(screen.getByText('Basic Information')).toBeInTheDocument();
      expect(screen.getByText('Ingredients *')).toBeInTheDocument();
      expect(screen.getByText('Instructions *')).toBeInTheDocument();
      expect(screen.getByText('Visibility')).toBeInTheDocument();
    });

    it('should render all form fields', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      // Basic Information
      expect(screen.getByLabelText(/recipe title/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
      
      // Cooking Details (part of Basic Information)
      expect(screen.getByLabelText(/preparation time/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/cooking time/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/servings/i)).toBeInTheDocument();
      expect(screen.getByText(/difficulty level/i)).toBeInTheDocument();
      
      // Additional Settings (part of Basic Information)
      expect(screen.getByLabelText(/image url/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/make this recipe public/i)).toBeInTheDocument();
    });

    it('should render submit button', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      expect(screen.getByRole('button', { name: /create recipe/i })).toBeInTheDocument();
    });
  });

  describe('Form Interactions', () => {
    it('should handle title input change', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const titleInput = screen.getByLabelText(/recipe title/i);
      fireEvent.change(titleInput, { target: { value: 'New Recipe Title' } });
      
      expect(titleInput).toHaveValue('New Recipe Title');
    });

    it('should handle description input change', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const descriptionInput = screen.getByLabelText(/description/i);
      fireEvent.change(descriptionInput, { target: { value: 'New description' } });
      
      expect(descriptionInput).toHaveValue('New description');
    });

    it('should handle preparation time change', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const prepTimeInput = screen.getByLabelText(/preparation time/i);
      fireEvent.change(prepTimeInput, { target: { value: '45' } });
      
      expect(prepTimeInput).toHaveValue(45);
    });

    it('should handle cooking time change', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const cookTimeInput = screen.getByLabelText(/cooking time/i);
      fireEvent.change(cookTimeInput, { target: { value: '60' } });
      
      expect(cookTimeInput).toHaveValue(60);
    });

    it('should handle servings change', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const servingsInput = screen.getByLabelText(/servings/i);
      fireEvent.change(servingsInput, { target: { value: '6' } });
      
      expect(servingsInput).toHaveValue(6);
    });

    it('should handle image URL change', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const imageUrlInput = screen.getByLabelText(/image url/i);
      fireEvent.change(imageUrlInput, { target: { value: 'https://example.com/image.jpg' } });
      
      expect(imageUrlInput).toHaveValue('https://example.com/image.jpg');
    });

    it('should handle public/private toggle', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const publicToggle = screen.getByLabelText(/make this recipe public/i);
      fireEvent.click(publicToggle);
      
      expect(publicToggle).not.toBeChecked();
    });
  });

  describe('Ingredients Management', () => {
    it('should add new ingredient', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const addButton = screen.getByRole('button', { name: /add ingredient/i });
      fireEvent.click(addButton);
      
      // Should have 2 ingredient rows (initial + added)
      const nameInputs = screen.getAllByPlaceholderText(/e\.g\., Flour/i);
      expect(nameInputs.length).toBe(2);
    });

    it('should remove ingredient when more than one exists', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      // First add an ingredient
      const addButton = screen.getByRole('button', { name: /add ingredient/i });
      fireEvent.click(addButton);
      
      // Then remove it
      const removeButtons = screen.getAllByRole('button', { name: /remove/i });
      fireEvent.click(removeButtons[0]);
      
      // Should be back to 1 ingredient
      const nameInputs = screen.getAllByPlaceholderText(/e\.g\., Flour/i);
      expect(nameInputs.length).toBe(1);
    });

    it('should handle ingredient name change', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const nameInputs = screen.getAllByPlaceholderText(/e\.g\., Flour/i);
      fireEvent.change(nameInputs[0], { target: { value: 'Flour' } });
      
      expect(nameInputs[0]).toHaveValue('Flour');
    });

    it('should handle ingredient amount change', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const amountInputs = screen.getAllByPlaceholderText(/e\.g\., 2 cups/i);
      fireEvent.change(amountInputs[0], { target: { value: '2 cups' } });
      
      expect(amountInputs[0]).toHaveValue('2 cups');
    });
  });

  describe('Instructions Management', () => {
    it('should add new instruction', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const addButton = screen.getByRole('button', { name: /add step/i });
      fireEvent.click(addButton);
      
      // Should have 2 instruction rows (initial + added)
      const instructionInputs = screen.getAllByPlaceholderText(/Step \d+\.\.\./i);
      expect(instructionInputs.length).toBe(2);
    });

    it('should remove instruction when more than one exists', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      // First add an instruction
      const addButton = screen.getByRole('button', { name: /add step/i });
      fireEvent.click(addButton);
      
      // Then remove it
      const removeButtons = screen.getAllByRole('button', { name: /remove/i });
      fireEvent.click(removeButtons[removeButtons.length - 1]); // Last remove button is for instruction
      
      // Should be back to 1 instruction
      const instructionInputs = screen.getAllByPlaceholderText(/Step \d+\.\.\./i);
      expect(instructionInputs.length).toBe(1);
    });

    it('should handle instruction change', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      const instructionInputs = screen.getAllByPlaceholderText(/Step 1\.\.\./i);
      fireEvent.change(instructionInputs[0], { target: { value: 'Mix ingredients' } });
      
      expect(instructionInputs[0]).toHaveValue('Mix ingredients');
    });
  });

  describe('Form Validation', () => {
    // it('should show error when title is empty', async () => {
    //   const mockNavigate = vi.fn();
    //   vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
    //   renderWithRouter(<RecipeCreatePage />);
      
    //   // Debug: log what's rendered
    //   screen.debug();
      
    //   const submitButton = screen.getByRole('button', { name: /create recipe/i });
      
    //   // Debug: check if button is found
    //   console.log('Submit button found:', !!submitButton);
      
    //   fireEvent.click(submitButton);
      
    //   // Debug: log what's rendered after click
    //   screen.debug();
      
    //   await waitFor(() => {
    //     expect(screen.getByText('Recipe title is required')).toBeInTheDocument();
    //   });
    // });

    it('should show error when ingredient is missing name or amount', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeCreatePage />);
      
      // Fill title but leave ingredient empty
      const titleInput = screen.getByLabelText(/recipe title/i);
      fireEvent.change(titleInput, { target: { value: 'Test Recipe' } });
      
      // Trigger form submission to validate
      const form = document.querySelector('form');
      fireEvent.submit(form!);
      
      await waitFor(() => {
        expect(screen.getByText('All ingredients must have both name and amount')).toBeInTheDocument();
      });
    });

    it('should show error when instruction is empty', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeCreatePage />);
      
      // Fill title and ingredient but leave instruction empty
      const titleInput = screen.getByLabelText(/recipe title/i);
      fireEvent.change(titleInput, { target: { value: 'Test Recipe' } });
      
      const nameInput = screen.getByPlaceholderText(/e\.g\., Flour/i);
      fireEvent.change(nameInput, { target: { value: 'Flour' } });
      
      const amountInput = screen.getByPlaceholderText(/e\.g\., 2 cups/i);
      fireEvent.change(amountInput, { target: { value: '2 cups' } });
      
      // Trigger form submission to validate
      const form = document.querySelector('form');
      fireEvent.submit(form!);
      
      await waitFor(() => {
        expect(screen.getByText('All instructions must not be empty')).toBeInTheDocument();
      });
    });

    it('should show error when preparation time is invalid', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeCreatePage />);
      
      // Fill required fields
      const titleInput = screen.getByLabelText(/recipe title/i);
      fireEvent.change(titleInput, { target: { value: 'Test Recipe' } });
      
      const nameInput = screen.getByPlaceholderText(/e\.g\., Flour/i);
      fireEvent.change(nameInput, { target: { value: 'Flour' } });
      
      const amountInput = screen.getByPlaceholderText(/e\.g\., 2 cups/i);
      fireEvent.change(amountInput, { target: { value: '2 cups' } });
      
      const instructionInput = screen.getByPlaceholderText(/Step 1\.\.\./i);
      fireEvent.change(instructionInput, { target: { value: 'Mix ingredients' } });
      
      // Set invalid preparation time
      const prepTimeInput = screen.getByLabelText(/preparation time/i);
      fireEvent.change(prepTimeInput, { target: { value: '0' } });
      
      // Trigger form submission to validate
      const form = document.querySelector('form');
      fireEvent.submit(form!);
      
      await waitFor(() => {
        expect(screen.getByText('Preparation and cooking times must be greater than 0')).toBeInTheDocument();
      });
    });

    it('should show error when servings is invalid', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeCreatePage />);
      
      // Fill required fields
      const titleInput = screen.getByLabelText(/recipe title/i);
      fireEvent.change(titleInput, { target: { value: 'Test Recipe' } });
      
      const nameInput = screen.getByPlaceholderText(/e\.g\., Flour/i);
      fireEvent.change(nameInput, { target: { value: 'Flour' } });
      
      const amountInput = screen.getByPlaceholderText(/e\.g\., 2 cups/i);
      fireEvent.change(amountInput, { target: { value: '2 cups' } });
      
      const instructionInput = screen.getByPlaceholderText(/Step 1\.\.\./i);
      fireEvent.change(instructionInput, { target: { value: 'Mix ingredients' } });
      
      // Set invalid servings
      const servingsInput = screen.getByLabelText(/servings/i);
      fireEvent.change(servingsInput, { target: { value: '0' } });
      
      // Trigger form submission to validate
      const form = document.querySelector('form');
      fireEvent.submit(form!);
      
      await waitFor(() => {
        expect(screen.getByText('Servings must be greater than 0')).toBeInTheDocument();
      });
    });
  });

  describe('Form Submission', () => {
    it('should submit form successfully with valid data', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeCreatePage />);
      
      // Fill all required fields
      const titleInput = screen.getByLabelText(/recipe title/i);
      fireEvent.change(titleInput, { target: { value: 'Test Recipe' } });
      
      const descriptionInput = screen.getByLabelText(/description/i);
      fireEvent.change(descriptionInput, { target: { value: 'A test recipe' } });
      
      const nameInput = screen.getByPlaceholderText(/e\.g\., Flour/i);
      fireEvent.change(nameInput, { target: { value: 'Flour' } });
      
      const amountInput = screen.getByPlaceholderText(/e\.g\., 2 cups/i);
      fireEvent.change(amountInput, { target: { value: '2 cups' } });
      
      const instructionInput = screen.getByPlaceholderText(/Step 1\.\.\./i);
      fireEvent.change(instructionInput, { target: { value: 'Mix ingredients' } });
      
      const submitButton = screen.getByRole('button', { name: /create recipe/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.createRecipe)).toHaveBeenCalledWith({
          title: 'Test Recipe',
          description: 'A test recipe',
          ingredients: [{ name: 'Flour', amount: '2 cups' }],
          instructions: ['Mix ingredients'],
          preparation_time: 30,
          cooking_time: 30,
          servings: 4,
          difficulty_level: 'Easy',
          is_public: true,
          image_url: undefined,
          selectedTags: [],
          tag_ids: [],
        });
      });
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/recipes/123', {
          state: { message: 'Recipe created successfully!' }
        });
      });
    });

    it('should handle API error during submission', async () => {
      vi.mocked(apiClient.createRecipe).mockRejectedValue(new Error('API Error'));
      
      renderWithRouter(<RecipeCreatePage />);
      
      // Fill all required fields
      const titleInput = screen.getByLabelText(/recipe title/i);
      fireEvent.change(titleInput, { target: { value: 'Test Recipe' } });
      
      const nameInput = screen.getByPlaceholderText(/e\.g\., Flour/i);
      fireEvent.change(nameInput, { target: { value: 'Flour' } });
      
      const amountInput = screen.getByPlaceholderText(/e\.g\., 2 cups/i);
      fireEvent.change(amountInput, { target: { value: '2 cups' } });
      
      const instructionInput = screen.getByPlaceholderText(/Step 1\.\.\./i);
      fireEvent.change(instructionInput, { target: { value: 'Mix ingredients' } });
      
      const submitButton = screen.getByRole('button', { name: /create recipe/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to create recipe')).toBeInTheDocument();
      });
    });

    it('should handle ApiError during submission', async () => {
      vi.mocked(apiClient.createRecipe).mockRejectedValue(new Error('Validation failed'));
      
      renderWithRouter(<RecipeCreatePage />);
      
      // Fill all required fields
      const titleInput = screen.getByLabelText(/recipe title/i);
      fireEvent.change(titleInput, { target: { value: 'Test Recipe' } });
      
      const nameInput = screen.getByPlaceholderText(/e\.g\., Flour/i);
      fireEvent.change(nameInput, { target: { value: 'Flour' } });
      
      const amountInput = screen.getByPlaceholderText(/e\.g\., 2 cups/i);
      fireEvent.change(amountInput, { target: { value: '2 cups' } });
      
      const instructionInput = screen.getByPlaceholderText(/Step 1\.\.\./i);
      fireEvent.change(instructionInput, { target: { value: 'Mix ingredients' } });
      
      const submitButton = screen.getByRole('button', { name: /create recipe/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to create recipe')).toBeInTheDocument();
      });
    });

    it('should disable form during submission', async () => {
      vi.mocked(apiClient.createRecipe).mockImplementation(() => new Promise(() => {})); // Never resolves
      
      renderWithRouter(<RecipeCreatePage />);
      
      // Fill all required fields
      const titleInput = screen.getByLabelText(/recipe title/i);
      fireEvent.change(titleInput, { target: { value: 'Test Recipe' } });
      
      const nameInput = screen.getByPlaceholderText(/e\.g\., Flour/i);
      fireEvent.change(nameInput, { target: { value: 'Flour' } });
      
      const amountInput = screen.getByPlaceholderText(/e\.g\., 2 cups/i);
      fireEvent.change(amountInput, { target: { value: '2 cups' } });
      
      const instructionInput = screen.getByPlaceholderText(/Step 1\.\.\./i);
      fireEvent.change(instructionInput, { target: { value: 'Mix ingredients' } });
      
      const submitButton = screen.getByRole('button', { name: /create recipe/i });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(submitButton).toBeDisabled();
        expect(titleInput).toBeDisabled();
      });
    });
  });

  // describe('Form State Management', () => {
  //   it('should clear error when form is resubmitted', async () => {
  //     const mockNavigate = vi.fn();
  //     vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
  //     renderWithRouter(<RecipeCreatePage />);
      
  //     // First submit with invalid data to trigger error
  //     const submitButton = screen.getByRole('button', { name: /create recipe/i });
  //     fireEvent.click(submitButton);
      
  //     await waitFor(() => {
  //       expect(screen.getByText('Recipe title is required')).toBeInTheDocument();
  //     });
      
  //     // Then fill required fields and submit again
  //     const titleInput = screen.getByLabelText(/recipe title/i);
  //     fireEvent.change(titleInput, { target: { value: 'Test Recipe' } });
      
  //     const nameInput = screen.getByPlaceholderText(/e\.g\., Flour/i);
  //     fireEvent.change(nameInput, { target: { value: 'Flour' } });
      
  //     const amountInput = screen.getByPlaceholderText(/e\.g\., 2 cups/i);
  //     fireEvent.change(amountInput, { target: { value: '2 cups' } });
      
  //     const instructionInput = screen.getByPlaceholderText(/Step 1\.\.\./i);
  //     fireEvent.change(instructionInput, { target: { value: 'Mix ingredients' } });
      
  //     fireEvent.click(submitButton);
      
  //     await waitFor(() => {
  //       expect(screen.queryByText('Recipe title is required')).not.toBeInTheDocument();
  //     });
  //   });
  // });

  describe('Debug', () => {
    it('should render all form sections', () => {
      renderWithRouter(<RecipeCreatePage />);
      
      // Debug: log what's actually rendered
      screen.debug();
      
      // Check if all sections are present
      expect(screen.getByText('Basic Information')).toBeInTheDocument();
      expect(screen.getByText('Ingredients *')).toBeInTheDocument();
      expect(screen.getByText('Instructions *')).toBeInTheDocument();
      expect(screen.getByText('Visibility')).toBeInTheDocument();
    });
  });
});
