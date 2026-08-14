import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { render } from '../../setup/test-utils';
import { RatingStars } from '../../../src/components/RecipeInteractions/RatingStars';
import { apiClient } from '../../../src/lib/api-client';

// Mock apiClient
vi.mock('../../../src/lib/api-client', () => ({
  apiClient: {
    setRating: vi.fn(),
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

describe('RatingStars', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders initial state correctly without details', () => {
    render(<RatingStars recipeId={1} initialAverage={3.5} initialCount={10} showDetails={false} />);
    
    const buttons = screen.getAllByRole('button');
    expect(buttons).toHaveLength(5);
    // 3.5 should round to 4 stars filled
    expect(buttons[3].querySelector('svg')).toHaveClass('fill-yellow-400');
    expect(buttons[4].querySelector('svg')).not.toHaveClass('fill-yellow-400');
  });

  it('renders details correctly', () => {
    render(<RatingStars recipeId={1} initialAverage={3.5} initialCount={10} showDetails={true} />);
    
    expect(screen.getByText('3.5')).toBeInTheDocument();
    expect(screen.getByText('(10 ratings)')).toBeInTheDocument();
  });

  it('handles rating a recipe for the first time', async () => {
    (apiClient.setRating as any).mockResolvedValueOnce({});
    
    render(
      <RatingStars 
        recipeId={1} 
        initialAverage={4} 
        initialCount={2} 
        initialUserRating={null} 
      />
    );
    
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[4]); // Rate 5 stars
    
    expect(apiClient.setRating).toHaveBeenCalledWith(1, 5);
    
    await waitFor(() => {
      // average should be (4 * 2 + 5) / 3 = 4.33...
      expect(screen.getByText('4.3')).toBeInTheDocument();
    });
  });

  it('handles changing an existing rating', async () => {
    (apiClient.setRating as any).mockResolvedValueOnce({});
    
    render(
      <RatingStars 
        recipeId={1} 
        initialAverage={4} 
        initialCount={2} 
        initialUserRating={4} 
      />
    );
    
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[2]); // Change rating to 3 stars
    
    expect(apiClient.setRating).toHaveBeenCalledWith(1, 3);
    
    await waitFor(() => {
      // average should be (4 * 2 - 4 + 3) / 2 = 3.5
      expect(screen.getByText('3.5')).toBeInTheDocument();
    });
  });

  it('is disabled when readOnly is true', () => {
    render(<RatingStars recipeId={1} readOnly={true} />);
    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).toBeDisabled();
    });
  });

  it('is disabled when unauthenticated', async () => {
    const { useAuth } = await import('../../../src/contexts/AuthContext');
    (useAuth as any).mockReturnValue({ isAuthenticated: false });

    render(<RatingStars recipeId={1} />);
    const buttons = screen.getAllByRole('button');
    buttons.forEach((button) => {
      expect(button).toBeDisabled();
    });
  });

  it('handles rating error', async () => {
    const { useAuth } = await import('../../../src/contexts/AuthContext');
    (useAuth as any).mockReturnValue({ isAuthenticated: true });
    
    (apiClient.setRating as any).mockRejectedValueOnce(new Error('Rating failed'));

    render(
      <RatingStars 
        recipeId={1} 
        initialAverage={4} 
        initialCount={2} 
        initialUserRating={null} 
      />
    );
    
    const buttons = screen.getAllByRole('button');
    fireEvent.click(buttons[4]); // Rate 5 stars
    
    expect(apiClient.setRating).toHaveBeenCalledWith(1, 5);
    
    await waitFor(() => {
      // average should not be updated on error (stays at 4.0)
      expect(screen.getByText('4.0')).toBeInTheDocument();
    });
  });
});
