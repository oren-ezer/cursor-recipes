import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { render } from '../../setup/test-utils';
import { CommentSection } from '../../../src/components/RecipeInteractions/CommentSection';
import { apiClient } from '../../../src/lib/api-client';
import { useAuth } from '../../../src/contexts/AuthContext';

// Mock AuthContext
vi.mock('../../../src/contexts/AuthContext', async () => {
  const actual = await vi.importActual('../../../src/contexts/AuthContext');
  return {
    ...actual,
    useAuth: vi.fn(),
  };
});

vi.mock('../../../src/lib/api-client', () => ({
  apiClient: {
    getComments: vi.fn(),
    addComment: vi.fn(),
    updateComment: vi.fn(),
    deleteComment: vi.fn(),
    toggleCommentReaction: vi.fn(),
  },
}));

const mockComments = [
  {
    id: 1,
    recipe_id: 1,
    user_id: 'user-123',
    user_full_name: 'John Doe',
    content: 'First comment',
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-01-01T00:00:00Z',
  },
  {
    id: 2,
    recipe_id: 1,
    user_id: 'user-456',
    user_full_name: 'Jane Smith',
    content: 'Second comment',
    created_at: '2023-01-02T00:00:00Z',
    updated_at: '2023-01-02T00:00:00Z',
  }
];

describe('CommentSection', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads and displays comments on mount', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: false, user: null, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getComments as any).mockResolvedValueOnce(mockComments);

    render(<CommentSection recipeId={1} />);

    expect(screen.getByText('Loading comments...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('First comment')).toBeInTheDocument();
      expect(screen.getByText('Second comment')).toBeInTheDocument();
    });

    expect(apiClient.getComments).toHaveBeenCalledWith(1);
    expect(screen.getByText('2')).toBeInTheDocument(); // Count badge
  });

  it('displays empty state if no comments', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: null, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getComments as any).mockResolvedValueOnce([]);

    render(<CommentSection recipeId={1} />);

    await waitFor(() => {
      expect(screen.getByText('No comments yet. Be the first to share your thoughts!')).toBeInTheDocument();
    });
  });

  it('shows login prompt for unauthenticated users', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: false, user: null, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getComments as any).mockResolvedValueOnce([]);

    render(<CommentSection recipeId={1} />);

    await waitFor(() => {
      expect(screen.getByText('Please login to join the conversation.')).toBeInTheDocument();
    });
  });

  it('allows authenticated user to post a comment', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-123' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getComments as any).mockResolvedValueOnce([]);
    
    const newComment = {
      id: 3,
      recipe_id: 1,
      user_id: 'user-123',
      user_full_name: 'John Doe',
      content: 'New posted comment',
      created_at: '2023-01-03T00:00:00Z',
      updated_at: '2023-01-03T00:00:00Z',
    };
    (apiClient.addComment as any).mockResolvedValueOnce(newComment);

    render(<CommentSection recipeId={1} />);

    await waitFor(() => {
      expect(screen.queryByText('Loading comments...')).not.toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText('Add a comment');
    fireEvent.change(textarea, { target: { value: 'New posted comment' } });

    const postBtn = screen.getByText('Post comment');
    fireEvent.click(postBtn);

    expect(apiClient.addComment).toHaveBeenCalledWith(1, 'New posted comment');

    await waitFor(() => {
      expect(screen.getByText('New posted comment')).toBeInTheDocument();
      expect(textarea).toHaveValue('');
    });
  });

  it('handles deleting a comment from the list', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-123' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getComments as any).mockResolvedValueOnce(mockComments);
    (apiClient.deleteComment as any).mockResolvedValueOnce({});
    window.confirm = vi.fn(() => true);

    render(<CommentSection recipeId={1} />);

    await waitFor(() => {
      expect(screen.getByText('First comment')).toBeInTheDocument();
    });

    // Hover over the first comment to show the actions
    fireEvent.mouseEnter(screen.getByText('First comment').closest('div')!);
    
    const deleteBtns = screen.getAllByTitle('Delete');
    fireEvent.click(deleteBtns[0]); // Delete first comment (John Doe's comment, which we own)

    await waitFor(() => {
      expect(screen.queryByText('First comment')).not.toBeInTheDocument();
    });
    expect(screen.getByText('Second comment')).toBeInTheDocument();
  });

  it('handles load comments error', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: false, user: null, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getComments as any).mockRejectedValueOnce(new Error('Load failed'));

    render(<CommentSection recipeId={1} />);

    await waitFor(() => {
      expect(screen.queryByText('Loading comments...')).not.toBeInTheDocument();
    });
  });

  it('handles post comment error', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-123' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getComments as any).mockResolvedValueOnce([]);
    (apiClient.addComment as any).mockRejectedValueOnce(new Error('Post failed'));

    render(<CommentSection recipeId={1} />);

    await waitFor(() => {
      expect(screen.queryByText('Loading comments...')).not.toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText('Add a comment');
    fireEvent.change(textarea, { target: { value: 'Failed comment' } });

    const postBtn = screen.getByText('Post comment');
    fireEvent.click(postBtn);

    await waitFor(() => {
      // The textarea should still have the text because submission failed
      expect(textarea).toHaveValue('Failed comment');
    });
    // Check that it's still showing empty state
    expect(screen.getByText('No comments yet. Be the first to share your thoughts!')).toBeInTheDocument();
  });

  it('handles updating a comment in the list', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-123' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getComments as any).mockResolvedValueOnce(mockComments);
    (apiClient.updateComment as any).mockResolvedValueOnce({ ...mockComments[0], content: 'Updated First comment' });

    render(<CommentSection recipeId={1} />);

    await waitFor(() => {
      expect(screen.getByText('First comment')).toBeInTheDocument();
    });

    // Hover over the first comment to show the actions
    fireEvent.mouseEnter(screen.getByText('First comment').closest('div')!);
    
    const editBtn = screen.getByTitle('Edit');
    fireEvent.click(editBtn);

    const textarea = screen.getByDisplayValue('First comment');
    fireEvent.change(textarea, { target: { value: 'Updated First comment' } });

    const saveBtn = screen.getByText('Save');
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(screen.getByText('Updated First comment')).toBeInTheDocument();
    });
  });

  it('does not post empty comment', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-123' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    (apiClient.getComments as any).mockResolvedValueOnce([]);

    render(<CommentSection recipeId={1} />);

    await waitFor(() => {
      expect(screen.queryByText('Loading comments...')).not.toBeInTheDocument();
    });

    const textarea = screen.getByPlaceholderText('Add a comment');
    fireEvent.change(textarea, { target: { value: '   ' } });

    const postBtn = screen.getByText('Post comment');
    fireEvent.click(postBtn);

    expect(apiClient.addComment).not.toHaveBeenCalled();
  });
});
