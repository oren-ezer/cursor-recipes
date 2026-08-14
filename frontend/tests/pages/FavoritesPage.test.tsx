import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { render } from '../setup/test-utils';
import FavoritesPage from '../../src/pages/FavoritesPage';
import { apiClient } from '../../src/lib/api-client';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../src/contexts/AuthContext';

vi.mock('../../src/lib/api-client', () => ({
  apiClient: {
    getMyFavorites: vi.fn(),
    getRecipe: vi.fn(),
  },
}));

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: vi.fn(),
  };
});

// Mock AuthContext
vi.mock('../../src/contexts/AuthContext', async () => {
  const actual = await vi.importActual('../../src/contexts/AuthContext');
  return {
    ...actual,
    useAuth: vi.fn(),
  };
});

describe('FavoritesPage', () => {
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNavigate).mockReturnValue(mockNavigate);
  });

  it('redirects to login if not authenticated', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: false, user: null, login: vi.fn(), logout: vi.fn(), isLoading: false });

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('displays empty state if no favorites', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-1' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getMyFavorites as any).mockResolvedValueOnce([]);

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText('No favorites yet.')).toBeInTheDocument();
    });
  });

  it('fetches and displays favorite recipes', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-1' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getMyFavorites as any).mockResolvedValueOnce([1, 2]);
    (apiClient.getRecipe as any).mockImplementation((id: number) => {
      return Promise.resolve({
        id,
        title: `Recipe ${id}`,
        description: 'Description',
        ingredients: [],
        instructions: [],
        preparation_time: 10,
        cooking_time: 10,
        servings: 2,
        difficulty_level: 'Easy',
        user_id: 'user-1',
        created_at: '2023-01-01',
        updated_at: '2023-01-01',
        is_public: true,
        tags: [],
      });
    });

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText('Recipe 1')).toBeInTheDocument();
      expect(screen.getByText('Recipe 2')).toBeInTheDocument();
    });
  });

  it('displays error message if fetching fails', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-1' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getMyFavorites as any).mockRejectedValueOnce(new Error('Failed to fetch'));

    render(<FavoritesPage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to fetch')).toBeInTheDocument();
    });
  });
});
