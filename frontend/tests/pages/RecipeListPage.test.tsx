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
    getRecipes: vi.fn(),
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
import RecipeListPage from '../../src/pages/RecipeListPage';
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

const mockPublicRecipes = [
  {
    id: 1,
    title: 'Public Recipe 1',
    description: 'A delicious public recipe',
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
    user_id: '2', // Different user
    is_public: true,
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
  {
    id: 2,
    title: 'Public Recipe 2',
    description: 'Another delicious public recipe',
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
    user_id: '3', // Different user
    is_public: true,
    created_at: '2023-01-02T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z',
  },
];

describe('RecipeListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    vi.mocked(useAuth).mockReturnValue(createMockAuth(false)); // Default to unauthenticated
    vi.mocked(useNavigate).mockReturnValue(vi.fn());
    vi.mocked(apiClient.getRecipes).mockResolvedValue(mockPublicRecipes);
  });

  describe('Authentication', () => {
    it('should render when user is not authenticated', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Recipes' })).toBeInTheDocument();
        expect(screen.getByText('Discover and explore delicious recipes from our community.')).toBeInTheDocument();
      });
    });

    it('should render when user is authenticated', async () => {
      vi.mocked(useAuth).mockReturnValue(createMockAuth(true, { id: 1, email: 'test@example.com' }));
      
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'Recipes' })).toBeInTheDocument();
        expect(screen.getByText('Discover and explore delicious recipes from our community.')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading state initially', () => {
      vi.mocked(apiClient.getRecipes).mockImplementation(() => new Promise(() => {})); // Never resolves
      
      renderWithRouter(<RecipeListPage />);
      
      expect(screen.getByText('Loading recipes...')).toBeInTheDocument();
    });
  });

  describe('Data Loading', () => {
    it('should fetch recipes on mount', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.getRecipes)).toHaveBeenCalled();
      });
    });

    it('should display recipes when data is loaded', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Public Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Public Recipe 2')).toBeInTheDocument();
        expect(screen.getByText('A delicious public recipe')).toBeInTheDocument();
        expect(screen.getByText('Another delicious public recipe')).toBeInTheDocument();
      });
    });

    it('should show error when recipe fetch fails', async () => {
      vi.mocked(apiClient.getRecipes).mockRejectedValue(new Error('Failed to fetch recipes'));
      
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to fetch recipes')).toBeInTheDocument();
      });
    });

    it('should show empty state when no recipes exist', async () => {
      vi.mocked(apiClient.getRecipes).mockResolvedValue([]);
      
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByText('No recipes available yet. Be the first to create one!')).toBeInTheDocument();
      });
    });
  });

  describe('Search Functionality', () => {
    it('should render search input', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText('Search recipes...')).toBeInTheDocument();
      });
    });

    it('should filter recipes by title', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Public Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Public Recipe 2')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText('Search recipes...');
      fireEvent.change(searchInput, { target: { value: 'Recipe 1' } });
      
      await waitFor(() => {
        expect(screen.getByText('Public Recipe 1')).toBeInTheDocument();
        expect(screen.queryByText('Public Recipe 2')).not.toBeInTheDocument();
      });
    });

    it('should filter recipes by description', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Public Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Public Recipe 2')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText('Search recipes...');
      fireEvent.change(searchInput, { target: { value: 'delicious' } });
      
      await waitFor(() => {
        expect(screen.getByText('Public Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Public Recipe 2')).toBeInTheDocument();
      });
    });

    it('should show no results message when search has no matches', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Public Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Public Recipe 2')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText('Search recipes...');
      fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
      
      await waitFor(() => {
        expect(screen.getByText('No recipes match your search.')).toBeInTheDocument();
        expect(screen.queryByText('Public Recipe 1')).not.toBeInTheDocument();
        expect(screen.queryByText('Public Recipe 2')).not.toBeInTheDocument();
      });
    });

    it('should be case insensitive', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Public Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Public Recipe 2')).toBeInTheDocument();
      });
      
      const searchInput = screen.getByPlaceholderText('Search recipes...');
      fireEvent.change(searchInput, { target: { value: 'RECIPE 1' } });
      
      await waitFor(() => {
        expect(screen.getByText('Public Recipe 1')).toBeInTheDocument();
        expect(screen.queryByText('Public Recipe 2')).not.toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('should show create recipe button when user is authenticated', async () => {
      vi.mocked(useAuth).mockReturnValue(createMockAuth(true, { id: 1, email: 'test@example.com' }));
      
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create recipe/i })).toBeInTheDocument();
      });
    });

    it('should not show create recipe button when user is not authenticated', async () => {
      vi.mocked(useAuth).mockReturnValue(createMockAuth(false));
      
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /create recipe/i })).not.toBeInTheDocument();
      });
    });

    it('should navigate to create recipe page when button is clicked', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      vi.mocked(useAuth).mockReturnValue(createMockAuth(true, { id: 1, email: 'test@example.com' }));
      
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        const createButton = screen.getByRole('button', { name: /create recipe/i });
        fireEvent.click(createButton);
        expect(mockNavigate).toHaveBeenCalledWith('/recipes/new');
      });
    });
  });

  describe('Recipe Display', () => {
    it('should display recipe cards with correct data', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        // Check that both recipes are displayed
        expect(screen.getByText('Public Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Public Recipe 2')).toBeInTheDocument();
        
        // Check descriptions
        expect(screen.getByText('A delicious public recipe')).toBeInTheDocument();
        expect(screen.getByText('Another delicious public recipe')).toBeInTheDocument();
        
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

    it('should not show delete buttons for public recipes', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        // Public recipes should not have delete buttons
        expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
      });
    });

    it('should show view buttons for public recipes', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        // Should have view buttons for each recipe (public recipes only have view buttons)
        const viewButtons = screen.getAllByRole('button', { name: /view recipe/i });
        expect(viewButtons.length).toBe(2); // One for each recipe
      });
    });
  });

  describe('Recipe Card Integration', () => {
    it('should render RecipeCard components with correct props', async () => {
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        // Check that RecipeCard components are rendered with the correct data
        expect(screen.getByText('Public Recipe 1')).toBeInTheDocument();
        expect(screen.getByText('Public Recipe 2')).toBeInTheDocument();
        
        // Check that the cards have the default variant (no delete buttons)
        expect(screen.queryByRole('button', { name: /delete/i })).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle ApiError during fetch', async () => {
      const apiError = new Error('API Error');
      apiError.name = 'ApiError';
      vi.mocked(apiClient.getRecipes).mockRejectedValue(apiError);
      
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to fetch recipes')).toBeInTheDocument();
      });
    });

    it('should handle generic error during fetch', async () => {
      vi.mocked(apiClient.getRecipes).mockRejectedValue(new Error('Network error'));
      
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to fetch recipes')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty recipe list', async () => {
      vi.mocked(apiClient.getRecipes).mockResolvedValue([]);
      
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByText('No recipes available yet. Be the first to create one!')).toBeInTheDocument();
        expect(screen.queryByText('Public Recipe 1')).not.toBeInTheDocument();
        expect(screen.queryByText('Public Recipe 2')).not.toBeInTheDocument();
      });
    });

    it('should handle recipe with missing optional fields', async () => {
      const recipeWithMissingFields = {
        id: 3,
        title: 'Minimal Public Recipe',
        description: '',
        preparation_time: 0,
        cooking_time: 0,
        servings: 1,
        difficulty_level: 'Easy',
        ingredients: [],
        instructions: [],
        image_url: undefined,
        user_id: '4',
        is_public: true,
        created_at: '2023-01-03T00:00:00Z',
        updated_at: '2023-01-03T00:00:00Z',
      };
      
      vi.mocked(apiClient.getRecipes).mockResolvedValue([recipeWithMissingFields]);
      
      renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Minimal Public Recipe')).toBeInTheDocument();
      });
    });
  });

  describe('Permissions', () => {
    it('should show create button only for authenticated users', async () => {
      // Test unauthenticated user
      vi.mocked(useAuth).mockReturnValue(createMockAuth(false));
      
      const { rerender } = renderWithRouter(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /create recipe/i })).not.toBeInTheDocument();
      });
      
      // Test authenticated user
      vi.mocked(useAuth).mockReturnValue(createMockAuth(true, { id: 1, email: 'test@example.com' }));
      
      rerender(<RecipeListPage />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /create recipe/i })).toBeInTheDocument();
      });
    });
  });
});
