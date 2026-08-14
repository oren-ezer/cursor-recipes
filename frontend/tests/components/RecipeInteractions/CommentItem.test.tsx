import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { render } from '../../setup/test-utils';
import { CommentItem } from '../../../src/components/RecipeInteractions/CommentItem';
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
    updateComment: vi.fn(),
    deleteComment: vi.fn(),
    toggleCommentReaction: vi.fn(),
  },
}));

const mockComment = {
  id: 1,
  recipe_id: 1,
  user_id: 'user-123',
  user_full_name: 'John Doe',
  content: 'This is a test comment',
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z',
  reactions: {
    counts: { like: 2 },
    user_reaction: 'like',
  },
};

describe('CommentItem', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders comment content and user details', () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-456' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={vi.fn()} 
        onDelete={vi.fn()} 
      />
    );
    
    expect(screen.getByText('John Doe')).toBeInTheDocument();
    expect(screen.getByText('This is a test comment')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // like count
  });

  it('allows owner to edit comment', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-123' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    const mockOnUpdate = vi.fn();
    (apiClient.updateComment as any).mockResolvedValueOnce({ ...mockComment, content: 'Updated content' });

    render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={mockOnUpdate} 
        onDelete={vi.fn()} 
      />
    );

    // Hover to show actions
    fireEvent.mouseEnter(screen.getByText('This is a test comment').closest('div')!);
    
    const editBtn = screen.getByTitle('Edit');
    fireEvent.click(editBtn);

    const textarea = screen.getByDisplayValue('This is a test comment');
    fireEvent.change(textarea, { target: { value: 'Updated content' } });

    const saveBtn = screen.getByText('Save');
    fireEvent.click(saveBtn);

    expect(apiClient.updateComment).toHaveBeenCalledWith(1, 'Updated content');

    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalledWith({ ...mockComment, content: 'Updated content' });
    });
  });

  it('allows owner to delete comment', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-123' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    const mockOnDelete = vi.fn();
    window.confirm = vi.fn(() => true);
    (apiClient.deleteComment as any).mockResolvedValueOnce({});

    render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={vi.fn()} 
        onDelete={mockOnDelete} 
      />
    );

    // Hover to show actions
    fireEvent.mouseEnter(screen.getByText('This is a test comment').closest('div')!);
    
    const deleteBtn = screen.getByTitle('Delete');
    fireEvent.click(deleteBtn);

    expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete this comment?');
    expect(apiClient.deleteComment).toHaveBeenCalledWith(1);

    await waitFor(() => {
      expect(mockOnDelete).toHaveBeenCalledWith(1);
    });
  });

  it('allows authenticated user to add a reaction', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-456' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    const mockOnUpdate = vi.fn();
    (apiClient.toggleCommentReaction as any).mockResolvedValueOnce({ status: 'added' });

    render(
      <CommentItem 
        comment={{ ...mockComment, reactions: { counts: {}, user_reaction: undefined } }} 
        onUpdate={mockOnUpdate} 
        onDelete={vi.fn()} 
      />
    );

    const addReactionBtn = screen.getByTitle('Add reaction');
    fireEvent.click(addReactionBtn);

    const loveBtn = screen.getByTitle('Love');
    fireEvent.click(loveBtn);

    expect(apiClient.toggleCommentReaction).toHaveBeenCalledWith(1, 'love');

    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalledWith(expect.objectContaining({
        reactions: {
          counts: { love: 1 },
          user_reaction: 'love'
        }
      }));
    });
  });

  it('does not show edit/delete actions for non-owners (unless superuser)', () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-456' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={vi.fn()} 
        onDelete={vi.fn()} 
      />
    );

    fireEvent.mouseEnter(screen.getByText('This is a test comment').closest('div')!);
    expect(screen.queryByTitle('Edit')).not.toBeInTheDocument();
    expect(screen.queryByTitle('Delete')).not.toBeInTheDocument();
  });

  it('shows edit/delete actions for superuser', () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'admin-123', is_superuser: true }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={vi.fn()} 
        onDelete={vi.fn()} 
      />
    );

    fireEvent.mouseEnter(screen.getByText('This is a test comment').closest('div')!);
    expect(screen.getByTitle('Edit')).toBeInTheDocument();
    expect(screen.getByTitle('Delete')).toBeInTheDocument();
  });

  it('handles delete error', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-123' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    const mockOnDelete = vi.fn();
    window.confirm = vi.fn(() => true);
    (apiClient.deleteComment as any).mockRejectedValueOnce(new Error('Delete failed'));
    
    render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={vi.fn()} 
        onDelete={mockOnDelete} 
      />
    );

    fireEvent.mouseEnter(screen.getByText('This is a test comment').closest('div')!);
    const deleteBtn = screen.getByTitle('Delete');
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(mockOnDelete).not.toHaveBeenCalled();
    });
  });

  it('allows authenticated user to change a reaction', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-456' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    const mockOnUpdate = vi.fn();
    (apiClient.toggleCommentReaction as any).mockResolvedValueOnce({ status: 'added' });

    render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={mockOnUpdate} 
        onDelete={vi.fn()} 
      />
    );

    const addReactionBtn = screen.getByTitle('Add reaction');
    fireEvent.click(addReactionBtn);

    const loveBtn = screen.getByTitle('Love');
    fireEvent.click(loveBtn);

    expect(apiClient.toggleCommentReaction).toHaveBeenCalledWith(1, 'love');

    await waitFor(() => {
      expect(mockOnUpdate).toHaveBeenCalledWith(expect.objectContaining({
        reactions: {
          counts: { like: 1, love: 1 },
          user_reaction: 'love'
        }
      }));
    });
  });

  it('handles toggle reaction error', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-456' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    const mockOnUpdate = vi.fn();
    (apiClient.toggleCommentReaction as any).mockRejectedValueOnce(new Error('Reaction failed'));

    render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={mockOnUpdate} 
        onDelete={vi.fn()} 
      />
    );

    const addReactionBtn = screen.getByTitle('Add reaction');
    fireEvent.click(addReactionBtn);

    const loveBtn = screen.getByTitle('Love');
    fireEvent.click(loveBtn);

    await waitFor(() => {
      expect(mockOnUpdate).not.toHaveBeenCalled();
    });
  });

  it('does not save empty comment edit', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-123' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={vi.fn()} 
        onDelete={vi.fn()} 
      />
    );

    fireEvent.mouseEnter(screen.getByText('This is a test comment').closest('div')!);
    
    const editBtn = screen.getByTitle('Edit');
    fireEvent.click(editBtn);

    const textarea = screen.getByDisplayValue('This is a test comment');
    fireEvent.change(textarea, { target: { value: '   ' } });

    const saveBtn = screen.getByText('Save');
    fireEvent.click(saveBtn);

    expect(apiClient.updateComment).not.toHaveBeenCalled();
  });

  it('does not save if content is unchanged', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-123' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={vi.fn()} 
        onDelete={vi.fn()} 
      />
    );

    fireEvent.mouseEnter(screen.getByText('This is a test comment').closest('div')!);
    
    const editBtn = screen.getByTitle('Edit');
    fireEvent.click(editBtn);

    const saveBtn = screen.getByText('Save');
    fireEvent.click(saveBtn);

    expect(apiClient.updateComment).not.toHaveBeenCalled();
  });

  it('handles edit save error', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { uuid: 'user-123' }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    const mockOnUpdate = vi.fn();
    (apiClient.updateComment as any).mockRejectedValueOnce(new Error('Update failed'));

    render(
      <CommentItem 
        comment={mockComment} 
        onUpdate={mockOnUpdate} 
        onDelete={vi.fn()} 
      />
    );

    fireEvent.mouseEnter(screen.getByText('This is a test comment').closest('div')!);
    
    const editBtn = screen.getByTitle('Edit');
    fireEvent.click(editBtn);

    const textarea = screen.getByDisplayValue('This is a test comment');
    fireEvent.change(textarea, { target: { value: 'Updated content' } });

    const saveBtn = screen.getByText('Save');
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(mockOnUpdate).not.toHaveBeenCalled();
    });
  });
});
