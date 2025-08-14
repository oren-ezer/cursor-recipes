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
    getMyRecipes: vi.fn(),
    deleteRecipe: vi.fn(),
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

// Import after mocks
import MyRecipesPage from '../../src/pages/MyRecipesPage';
import { useAuth } from '../../src/contexts/AuthContext';
import { apiClient } from '../../src/lib/api-client';
import { useNavigate } from 'react-router-dom';

// Mock window.confirm
const mockConfirm = vi.fn();
Object.defineProperty(window, 'confirm', {
  value: mockConfirm,
  writable: true,
});

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

const mockRecipes = [
  {
    id: 1,
    title: 'Test Recipe 1',
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
    image_url: 'https://example.com/image1.jpg',
    user_id: '1',
    is_public: true,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
  {
    id: 2,
    title: 'Test Recipe 2',
    description: 'Another delicious test recipe',
    preparation_time: 20,
    cooking_time: 30,
    servings: 2,
    difficulty_level: 'Easy',
    ingredients: [
      { name: 'Ingredient 3', amount: '1 cup' },
    ],
    instructions: [
      'Step 1: Mix ingredients',
    ],
    image_url: 'https://example.com/image2.jpg',
    user_id: '1',
    is_public: false,
    created_at: '2023-01-02T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z',
  },
];

describe('MyRecipesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    vi.mocked(useAuth).mockReturnValue(createMockAuth(true, { id: 1, email: 'test@example.com' }));
    vi.mocked(useNavigate).mockReturnValue(vi.fn());
    vi.mocked(apiClient.getMyRecipes).mockResolvedValue(mockRecipes);
    vi.mocked(apiClient.deleteRecipe).mockResolvedValue(undefined);
    
    mockConfirm.mockReturnValue(true);
  });

  describe('Authentication', () => {
    it('should render when user is authenticated', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('My Recipes')).toBeInTheDocument();
        expect(screen.getByText('Manage and organize your personal recipe collection.')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading state initially', () => {
      vi.mocked(apiClient.getMyRecipes).mockImplementation(() => new Promise(() => {})); // Never resolves
      
      renderWithRouter(<MyRecipesPage />);
      
      expect(screen.getByText('Loading your recipes...')).toBeInTheDocument();
    });
  });

  describe('Data Loading', () => {
    it('should fetch recipes on mount', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.getMyRecipes)).toHaveBeenCalled();
      });
    });

    it('should display recipes when data is loaded', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Test Recipe 2')).toBeInTheDocument();
        expect(screen.getByText('A delicious test recipe')).toBeInTheDocument();
        expect(screen.getByText('Another delicious test recipe')).toBeInTheDocument();
      });
    });

    it('should show error when recipe fetch fails', async () => {
      vi.mocked(apiClient.getMyRecipes).mockRejectedValue(new Error('Failed to fetch recipes'));
      
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to fetch recipes')).toBeInTheDocument();
      });
    });

    it('should show empty state when no recipes exist', async () => {
      vi.mocked(apiClient.getMyRecipes).mockResolvedValue([]);
      
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('You haven\'t created any recipes yet. Start by creating your first recipe!')).toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    it('should render search input', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search your recipes...')).toBeInTheDocument();
      });
    });

    it('should filter recipes by title', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Test Recipe 2')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText('Search your recipes...');
      fireEvent.change(searchInput, { target: { value: 'Recipe 1' } });
      
      await waitFor(() => {
        expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
        expect(screen.queryByText('Test Recipe 2')).not.toBeInTheDocument();
      });
    });

    it('should filter recipes by description', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Test Recipe 2')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText('Search your recipes...');
      fireEvent.change(searchInput, { target: { value: 'delicious' } });
      
      await waitFor(() => {
        expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Test Recipe 2')).toBeInTheDocument();
      });
    });

    it('should show no results message when search has no matches', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Test Recipe 2')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText('Search your recipes...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
      
      await waitFor(() => {
        expect(screen.getByText('No recipes match your search.')).toBeInTheDocument();
        expect(screen.queryByText('Test Recipe 1')).not.toBeInTheDocument();
        expect(screen.queryByText('Test Recipe 2')).not.toBeInTheDocument();
      });
    });

    it('should be case insensitive', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Test Recipe 2')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText('Search your recipes...');
      fireEvent.change(searchInput, { target: { value: 'RECIPE 1' } });
      
      await waitFor(() => {
        expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
        expect(screen.queryByText('Test Recipe 2')).not.toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('should render create recipe button', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create recipe/i })).toBeInTheDocument();
      });
    });

    it('should navigate to create recipe page when button is clicked', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        const createButton = screen.getByRole('button', { name: /create recipe/i });
        fireEvent.click(createButton);
        expect(mockNavigate).toHaveBeenCalledWith('/recipes/new');
      });
    });
  });

  describe('Recipe Management', () => {
    it('should display recipe cards with correct data', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        // Check that both recipes are displayed
        expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Test Recipe 2')).toBeInTheDocument();
        
        // Check descriptions
        expect(screen.getByText('A delicious test recipe')).toBeInTheDocument();
        expect(screen.getByText('Another delicious test recipe')).toBeInTheDocument();
        
        // Check cooking times (format is "Prep: 30m", "Cook: 45m", etc.)
        expect(screen.getByText('Prep: 30m')).toBeInTheDocument(); // preparation time for recipe 1
        expect(screen.getByText('Cook: 45m')).toBeInTheDocument(); // cooking time for recipe 1
        expect(screen.getByText('Prep: 20m')).toBeInTheDocument(); // preparation time for recipe 2
        expect(screen.getByText('Cook: 30m')).toBeInTheDocument(); // cooking time for recipe 2
        
        // Check servings (format is "Serves: 4", "Serves: 2", etc.)
        expect(screen.getByText('Serves: 4')).toBeInTheDocument(); // servings for recipe 1
        expect(screen.getByText('Serves: 2')).toBeInTheDocument(); // servings for recipe 2
        
        // Check difficulty levels
        expect(screen.getByText('Medium')).toBeInTheDocument(); // difficulty for recipe 1
        expect(screen.getByText('Easy')).toBeInTheDocument(); // difficulty for recipe 2
      });
    });

    it('should show delete buttons for each recipe', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        expect(deleteButtons.length).toBe(2); // One for each recipe
      });
    });

    it('should show confirmation dialog when delete button is clicked', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        fireEvent.click(deleteButtons[0]);
        expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to delete "Test Recipe 1"?');
      });
    });

    it('should delete recipe when confirmation is accepted', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        fireEvent.click(deleteButtons[0]);
      });
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.deleteRecipe)).toHaveBeenCalledWith(1);
      });
      
      // Recipe should be removed from the list
      await waitFor(() => {
        expect(screen.queryByText('Test Recipe 1')).not.toBeInTheDocument();
        expect(screen.getByText('Test Recipe 2')).toBeInTheDocument();
      });
    });

    it('should not delete recipe when confirmation is cancelled', async () => {
      mockConfirm.mockReturnValue(false);
      
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        fireEvent.click(deleteButtons[0]);
      });
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.deleteRecipe)).not.toHaveBeenCalled();
      });
      
      // Recipe should still be in the list
      await waitFor(() => {
        expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Test Recipe 2')).toBeInTheDocument();
      });
    });

    it('should handle delete error gracefully', async () => {
      vi.mocked(apiClient.deleteRecipe).mockRejectedValue(new Error('Delete failed'));
      
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        fireEvent.click(deleteButtons[0]);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Failed to delete recipe')).toBeInTheDocument();
      });
      
      // When there's an error, recipes are not shown (component shows error instead of recipes)
      await waitFor(() => {
        expect(screen.queryByText('Test Recipe 1')).not.toBeInTheDocument();
        expect(screen.queryByText('Test Recipe 2')).not.toBeInTheDocument();
      });
    });
  });

  describe('Recipe Card Integration', () => {
    it('should render RecipeCard components with correct props', async () => {
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        // Check that RecipeCard components are rendered with the correct data
        expect(screen.getByText('Test Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Test Recipe 2')).toBeInTheDocument();
        
        // Check that the cards have the correct variant
        // This would be tested by checking the delete buttons are present
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        expect(deleteButtons.length).toBe(2);
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle ApiError during fetch', async () => {
      const apiError = new Error('API Error');
      apiError.name = 'ApiError';
      vi.mocked(apiClient.getMyRecipes).mockRejectedValue(apiError);
      
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to fetch recipes')).toBeInTheDocument();
      });
    });

    it('should handle generic error during fetch', async () => {
      vi.mocked(apiClient.getMyRecipes).mockRejectedValue(new Error('Network error'));
      
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to fetch recipes')).toBeInTheDocument();
      });
    });

    it('should handle ApiError during delete', async () => {
      const apiError = new Error('Delete failed');
      apiError.name = 'ApiError';
      vi.mocked(apiClient.deleteRecipe).mockRejectedValue(apiError);
      
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        const deleteButtons = screen.getAllByRole('button', { name: /delete/i });
        fireEvent.click(deleteButtons[0]);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Failed to delete recipe')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty recipe list', async () => {
      vi.mocked(apiClient.getMyRecipes).mockResolvedValue([]);
      
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('You haven\'t created any recipes yet. Start by creating your first recipe!')).toBeInTheDocument();
        expect(screen.queryByText('Test Recipe 1')).not.toBeInTheDocument();
        expect(screen.queryByText('Test Recipe 2')).not.toBeInTheDocument();
      });
    });

    it('should handle recipe with missing optional fields', async () => {
      const recipeWithMissingFields = {
        id: 3,
        title: 'Minimal Recipe',
        description: '',
        preparation_time: 0,
        cooking_time: 0,
        servings: 1,
        difficulty_level: 'Easy',
        ingredients: [],
        instructions: [],
        image_url: undefined,
        user_id: '1',
        is_public: true,
        created_at: '2023-01-03T00:00:00Z',
        updated_at: '2023-01-03T00:00:00Z',
      };
      
      vi.mocked(apiClient.getMyRecipes).mockResolvedValue([recipeWithMissingFields]);
      
      renderWithRouter(<MyRecipesPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Minimal Recipe')).toBeInTheDocument();
      });
    });
  });
});
