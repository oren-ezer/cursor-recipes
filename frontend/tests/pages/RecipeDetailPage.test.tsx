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
    useParams: vi.fn(),
    useNavigate: vi.fn(),
  };
});

// Import after mocks
import RecipeDetailPage from '../../src/pages/RecipeDetailPage';
import { useAuth } from '../../src/contexts/AuthContext';
import { apiClient } from '../../src/lib/api-client';
import { useParams, useNavigate } from 'react-router-dom';

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

// Helper function to create mock auth values
const createMockAuth = (isAuthenticated: boolean, user: any = null) => ({
  isAuthenticated,
  user,
  token: isAuthenticated ? 'mock-token' : null,
  login: vi.fn(),
  logout: vi.fn(),
  isLoading: false,
});

describe('RecipeDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    vi.mocked(useAuth).mockReturnValue(createMockAuth(false));
    
    vi.mocked(useParams).mockReturnValue({ recipeId: '123' });
    vi.mocked(useNavigate).mockReturnValue(vi.fn());
    
    vi.mocked(apiClient.getRecipe).mockResolvedValue(mockRecipe);
    vi.mocked(apiClient.deleteRecipe).mockResolvedValue(undefined);
    
    mockConfirm.mockReturnValue(true);
  });

  describe('Loading State', () => {
    it('should show loading message initially', () => {
      vi.mocked(apiClient.getRecipe).mockImplementation(() => new Promise(() => {})); // Never resolves
      
      renderWithRouter(<RecipeDetailPage />);
      
      expect(screen.getByText('Loading recipe...')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should show error message when recipe fetch fails', async () => {
      vi.mocked(apiClient.getRecipe).mockRejectedValue(new Error('Failed to fetch recipe'));
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Failed to fetch recipe')).toBeInTheDocument();
      });
    });

    it('should show "Recipe not found" when recipe is null', async () => {
      vi.mocked(apiClient.getRecipe).mockResolvedValue(null as any);
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Recipe not found')).toBeInTheDocument();
      });
    });

    it('should show back button on error', async () => {
      vi.mocked(apiClient.getRecipe).mockRejectedValue(new Error('Failed to fetch recipe'));
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const backButton = screen.getByRole('button', { name: /back to recipes/i });
        expect(backButton).toBeInTheDocument();
      });
    });
  });

  describe('Recipe Display', () => {
    it('should display recipe title and description', async () => {
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const recipeTitles = screen.getAllByText('Test Recipe');
        expect(recipeTitles).toHaveLength(2); // One in page title, one in RecipeCard
        const descriptions = screen.getAllByText('A delicious test recipe');
        expect(descriptions).toHaveLength(2); // One in page description, one in RecipeCard
      });
    });

    it('should display recipe information correctly', async () => {
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Recipe Information')).toBeInTheDocument();
        expect(screen.getByText('30 minutes')).toBeInTheDocument(); // preparation time
        expect(screen.getByText('45 minutes')).toBeInTheDocument(); // cooking time
        expect(screen.getByText('4 people')).toBeInTheDocument(); // servings
        const mediumElements = screen.getAllByText('Medium');
        expect(mediumElements).toHaveLength(2); // One in RecipeCard, one in Recipe Information
      });
    });

    it('should display ingredients correctly', async () => {
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Ingredients')).toBeInTheDocument();
        expect(screen.getByText('Ingredient 1')).toBeInTheDocument();
        expect(screen.getByText('2 cups')).toBeInTheDocument();
        expect(screen.getByText('Ingredient 2')).toBeInTheDocument();
        expect(screen.getByText('1 tbsp')).toBeInTheDocument();
      });
    });

    it('should display instructions correctly', async () => {
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Instructions')).toBeInTheDocument();
        expect(screen.getByText('Step 1: Do something')).toBeInTheDocument();
        expect(screen.getByText('Step 2: Do something else')).toBeInTheDocument();
        expect(screen.getByText('1')).toBeInTheDocument(); // step number
        expect(screen.getByText('2')).toBeInTheDocument(); // step number
      });
    });

    it('should show image availability when image_url exists', async () => {
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        expect(screen.getByText('Image:')).toBeInTheDocument();
        expect(screen.getByText('Available')).toBeInTheDocument();
      });
    });
  });

  describe('Time Formatting', () => {
    it('should format time correctly for minutes under 60', async () => {
      const shortRecipe = { ...mockRecipe, preparation_time: 30, cooking_time: 45 };
      vi.mocked(apiClient.getRecipe).mockResolvedValue(shortRecipe);
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        expect(screen.getByText('30 minutes')).toBeInTheDocument();
        expect(screen.getByText('45 minutes')).toBeInTheDocument();
      });
    });

    it('should format time correctly for hours', async () => {
      const longRecipe = { ...mockRecipe, preparation_time: 120, cooking_time: 90 };
      vi.mocked(apiClient.getRecipe).mockResolvedValue(longRecipe);
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        expect(screen.getByText('2 hours')).toBeInTheDocument();
        expect(screen.getByText('1 hour 30 minutes')).toBeInTheDocument();
      });
    });

    it('should format time correctly for single hour', async () => {
      const singleHourRecipe = { ...mockRecipe, preparation_time: 60, cooking_time: 60 };
      vi.mocked(apiClient.getRecipe).mockResolvedValue(singleHourRecipe);
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const hourElements = screen.getAllByText('1 hour');
        expect(hourElements).toHaveLength(2); // One for preparation time, one for cooking time
      });
    });
  });

  describe('Difficulty Color Coding', () => {
    it('should apply correct color for easy difficulty', async () => {
      const easyRecipe = { ...mockRecipe, difficulty_level: 'Easy' };
      vi.mocked(apiClient.getRecipe).mockResolvedValue(easyRecipe);
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const difficultyElements = screen.getAllByText('Easy');
        expect(difficultyElements).toHaveLength(2); // One in RecipeCard, one in Recipe Information
        difficultyElements.forEach(element => {
          expect(element).toHaveClass('text-green-600');
        });
      });
    });

    it('should apply correct color for medium difficulty', async () => {
      const mediumRecipe = { ...mockRecipe, difficulty_level: 'Medium' };
      vi.mocked(apiClient.getRecipe).mockResolvedValue(mediumRecipe);
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const difficultyElements = screen.getAllByText('Medium');
        expect(difficultyElements).toHaveLength(2); // One in RecipeCard, one in Recipe Information
        difficultyElements.forEach(element => {
          expect(element).toHaveClass('text-yellow-600');
        });
      });
    });

    it('should apply correct color for hard difficulty', async () => {
      const hardRecipe = { ...mockRecipe, difficulty_level: 'Hard' };
      vi.mocked(apiClient.getRecipe).mockResolvedValue(hardRecipe);
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const difficultyElements = screen.getAllByText('Hard');
        expect(difficultyElements).toHaveLength(2); // One in RecipeCard, one in Recipe Information
        difficultyElements.forEach(element => {
          expect(element).toHaveClass('text-red-600');
        });
      });
    });
  });

  describe('Navigation', () => {
    it('should navigate back to recipes when back button is clicked', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const backButton = screen.getByRole('button', { name: /back to recipes/i });
        fireEvent.click(backButton);
        expect(mockNavigate).toHaveBeenCalledWith('/recipes');
      });
    });

    it('should show "My Recipes" button when user is authenticated', async () => {
      vi.mocked(useAuth).mockReturnValue(createMockAuth(true, { id: 1, email: 'test@example.com' }));
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const myRecipesButton = screen.getByRole('button', { name: /my recipes/i });
        expect(myRecipesButton).toBeInTheDocument();
      });
    });

    it('should navigate to My Recipes when button is clicked', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      vi.mocked(useAuth).mockReturnValue(createMockAuth(true, { id: 1, email: 'test@example.com' }));
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const myRecipesButton = screen.getByRole('button', { name: /my recipes/i });
        fireEvent.click(myRecipesButton);
        expect(mockNavigate).toHaveBeenCalledWith('/recipes/my');
      });
    });
  });

  describe('Owner Actions', () => {
    beforeEach(() => {
      vi.mocked(useAuth).mockReturnValue(createMockAuth(true, { id: 1, email: 'test@example.com' }));
    });

    it('should show edit and delete buttons for recipe owner', async () => {
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /edit recipe/i })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /delete recipe/i })).toBeInTheDocument();
      });
    });

    it('should navigate to edit page when edit button is clicked', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const editButton = screen.getByRole('button', { name: /edit recipe/i });
        fireEvent.click(editButton);
        expect(mockNavigate).toHaveBeenCalledWith('/recipes/123/edit');
      });
    });

    it('should show confirmation dialog when delete button is clicked', async () => {
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const deleteButton = screen.getByRole('button', { name: /delete recipe/i });
        fireEvent.click(deleteButton);
        expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to delete "Test Recipe"?');
      });
    });

    it('should delete recipe and navigate when confirmed', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const deleteButton = screen.getByRole('button', { name: /delete recipe/i });
        fireEvent.click(deleteButton);
      });
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.deleteRecipe)).toHaveBeenCalledWith(123);
        expect(mockNavigate).toHaveBeenCalledWith('/recipes/my', {
          state: { message: 'Recipe deleted successfully' }
        });
      });
    });

    it('should not delete recipe when confirmation is cancelled', async () => {
      mockConfirm.mockReturnValue(false);
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const deleteButton = screen.getByRole('button', { name: /delete recipe/i });
        fireEvent.click(deleteButton);
      });
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.deleteRecipe)).not.toHaveBeenCalled();
      });
    });

    it('should handle delete error gracefully', async () => {
      vi.mocked(apiClient.deleteRecipe).mockRejectedValue(new Error('Delete failed'));
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        const deleteButton = screen.getByRole('button', { name: /delete recipe/i });
        fireEvent.click(deleteButton);
      });
      
      await waitFor(() => {
        expect(screen.getByText('Failed to delete recipe')).toBeInTheDocument();
      });
    });
  });

  describe('Non-Owner View', () => {
    it('should not show edit and delete buttons for non-owner', async () => {
      vi.mocked(useAuth).mockReturnValue(createMockAuth(true, { id: 2, email: 'other@example.com' }));
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /edit recipe/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /delete recipe/i })).not.toBeInTheDocument();
      });
    });

    it('should not show edit and delete buttons for unauthenticated user', async () => {
      vi.mocked(useAuth).mockReturnValue(createMockAuth(false));
      
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        expect(screen.queryByRole('button', { name: /edit recipe/i })).not.toBeInTheDocument();
        expect(screen.queryByRole('button', { name: /delete recipe/i })).not.toBeInTheDocument();
      });
    });
  });

  describe('Recipe Card Integration', () => {
    it('should render RecipeCard component with correct props', async () => {
      renderWithRouter(<RecipeDetailPage />);
      
      await waitFor(() => {
        // RecipeCard should be rendered with the recipe data
        // Use getAllByText since there are multiple elements with the same text
        const recipeTitles = screen.getAllByText('Test Recipe');
        expect(recipeTitles).toHaveLength(2); // One in page title, one in RecipeCard
        const descriptions = screen.getAllByText('A delicious test recipe');
        expect(descriptions).toHaveLength(2); // One in page description, one in RecipeCard
      });
    });
  });
});
