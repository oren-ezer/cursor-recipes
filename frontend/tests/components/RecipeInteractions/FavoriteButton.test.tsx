import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { render } from '../../setup/test-utils';
import { FavoriteButton } from '../../../src/components/RecipeInteractions/FavoriteButton';
import { apiClient } from '../../../src/lib/api-client';

// Mock apiClient
vi.mock('../../../src/lib/api-client', () => ({
  apiClient: {
    toggleFavorite: vi.fn(),
  },
}));

// Mock AuthContext
vi.mock('../../../src/contexts/AuthContext', async () => {
  const actual = await vi.importActual('../../../src/contexts/AuthContext');
  return {
    ...actual,
    useAuth: vi.fn(() => ({
      isAuthenticated: true,
    })),
  };
});

describe('FavoriteButton', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders correctly with initial un-favorited state', () => {
    render(<FavoriteButton recipeId={1} initialCount={5} initialIsFavorited={false} />);
    const button = screen.getByRole('button');
    expect(button).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    // check if un-favorited text or title exists
    expect(button).toHaveAttribute('title', 'Add to favorites');
  });

  it('renders correctly with initial favorited state', () => {
    render(<FavoriteButton recipeId={1} initialCount={10} initialIsFavorited={true} />);
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('title', 'Remove from favorites');
    expect(screen.getByText('10')).toBeInTheDocument();
  });

  it('handles toggle to favorited successfully', async () => {
    const mockOnToggle = vi.fn();
    (apiClient.toggleFavorite as any).mockResolvedValueOnce({ status: 'added' });

    render(
      <FavoriteButton
        recipeId={1}
        initialCount={5}
        initialIsFavorited={false}
        onToggle={mockOnToggle}
      />
    );

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(apiClient.toggleFavorite).toHaveBeenCalledWith(1);

    await waitFor(() => {
      expect(mockOnToggle).toHaveBeenCalledWith(true, 6);
    });

    expect(screen.getByText('6')).toBeInTheDocument();
    expect(button).toHaveAttribute('title', 'Remove from favorites');
  });

  it('handles toggle to un-favorited successfully', async () => {
    const mockOnToggle = vi.fn();
    (apiClient.toggleFavorite as any).mockResolvedValueOnce({ status: 'removed' });

    render(
      <FavoriteButton
        recipeId={1}
        initialCount={5}
        initialIsFavorited={true}
        onToggle={mockOnToggle}
      />
    );

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(apiClient.toggleFavorite).toHaveBeenCalledWith(1);

    await waitFor(() => {
      expect(mockOnToggle).toHaveBeenCalledWith(false, 4);
    });

    expect(screen.getByText('4')).toBeInTheDocument();
    expect(button).toHaveAttribute('title', 'Add to favorites');
  });

  it('does not toggle if unauthenticated', async () => {
    const { useAuth } = await import('../../../src/contexts/AuthContext');
    (useAuth as any).mockReturnValue({ isAuthenticated: false });

    render(<FavoriteButton recipeId={1} />);

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    fireEvent.click(button);

    expect(apiClient.toggleFavorite).not.toHaveBeenCalled();
  });

  it('handles toggle favorite error', async () => {
    const { useAuth } = await import('../../../src/contexts/AuthContext');
    (useAuth as any).mockReturnValue({ isAuthenticated: true });
    
    const mockOnToggle = vi.fn();
    (apiClient.toggleFavorite as any).mockRejectedValueOnce(new Error('Toggle failed'));

    render(
      <FavoriteButton
        recipeId={1}
        initialCount={5}
        initialIsFavorited={false}
        onToggle={mockOnToggle}
      />
    );

    const button = screen.getByRole('button');
    fireEvent.click(button);

    await waitFor(() => {
      expect(mockOnToggle).not.toHaveBeenCalled();
    });
  });
});
