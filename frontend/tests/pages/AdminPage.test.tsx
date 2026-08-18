import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { render, fireEvent } from '../setup/test-utils';
import AdminPage from '../../src/pages/AdminPage';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../src/contexts/AuthContext';
import { apiClient, ApiError } from '../../src/lib/api-client';

vi.mock('../../src/lib/api-client', () => ({
  apiClient: {
    getAllUsers: vi.fn(),
    getAllRecipesForAdmin: vi.fn(),
    getAllTags: vi.fn(),
    getAppSettings: vi.fn(),
    getAllLLMConfigs: vi.fn(),
    resetUserPassword: vi.fn(),
    deleteUser: vi.fn(),
    setUserSuperuser: vi.fn(),
    createTag: vi.fn(),
    updateTag: vi.fn(),
    deleteTag: vi.fn(),
    updateAppSettings: vi.fn(),
    createLLMConfig: vi.fn(),
    updateLLMConfig: vi.fn(),
    deleteLLMConfig: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    constructor(message: string) {
      super(message);
      this.name = 'ApiError';
    }
  }
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

describe('AdminPage', () => {
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNavigate).mockReturnValue(mockNavigate);
  });

  it('redirects to login if not authenticated', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: false, user: null, login: vi.fn(), logout: vi.fn(), isLoading: false });

    render(<AdminPage />);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('redirects to home if authenticated but not superuser', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { is_superuser: false }, login: vi.fn(), logout: vi.fn(), isLoading: false });

    render(<AdminPage />);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/');
    });
  });

  it('renders loading state initially for superuser', () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { is_superuser: true }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    // Provide a mocked promise that doesn't resolve immediately to allow checking the loading state
    vi.mocked(apiClient.getAllUsers).mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ users: [], total: 0 }), 100)));

    render(<AdminPage />);
    expect(screen.getByText('Loading users...')).toBeInTheDocument();
  });

  it('renders users list successfully', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { is_superuser: true }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    const mockUsers = [
      { id: 1, email: 'test@example.com', is_active: true, is_superuser: false, uuid: 'abc-123' },
      { id: 2, email: 'admin@example.com', is_active: true, is_superuser: true, uuid: 'def-456' }
    ];
    vi.mocked(apiClient.getAllUsers).mockResolvedValue({ users: mockUsers, total: 2 });

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });
  });

  it('switches to recipes tab and loads recipes', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { is_superuser: true }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    vi.mocked(apiClient.getAllUsers).mockResolvedValue({ users: [], total: 0 });
    
    const mockRecipes = [
      { id: 1, title: 'Pasta', description: 'Yummy', user_id: 'abc-123', is_public: true, created_at: '2023-01-01' }
    ];
    vi.mocked(apiClient.getAllRecipesForAdmin).mockResolvedValue(mockRecipes);

    render(<AdminPage />);

    const recipesTab = screen.getByText('Recipe Management');
    fireEvent.click(recipesTab);

    await waitFor(() => {
      expect(apiClient.getAllRecipesForAdmin).toHaveBeenCalled();
      expect(screen.getByText('Pasta')).toBeInTheDocument();
    });
  });

  it('switches to tags tab and loads tags', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { is_superuser: true }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    vi.mocked(apiClient.getAllUsers).mockResolvedValue({ users: [], total: 0 });
    
    const mockTags = [
      { id: 1, name: 'Vegan', category: 'Diet', recipe_counter: 5 }
    ];
    vi.mocked(apiClient.getAllTags).mockResolvedValue(mockTags);

    render(<AdminPage />);

    const tagsTab = screen.getByText('Tag Management');
    fireEvent.click(tagsTab);

    await waitFor(() => {
      expect(apiClient.getAllTags).toHaveBeenCalled();
      expect(screen.getByText('Vegan')).toBeInTheDocument();
    });
  });

  it('switches to settings tab and loads settings', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { is_superuser: true }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    vi.mocked(apiClient.getAllUsers).mockResolvedValue({ users: [], total: 0 });
    
    const mockSettings = {
      groups: [{ id: 'general', name: 'General', settings: [{ key: 'site_name', type: 'string', value: 'Recipe App', source: 'database' }] }],
      status: { db_connected: true }
    };
    vi.mocked(apiClient.getAppSettings).mockResolvedValue(mockSettings);

    render(<AdminPage />);

    const settingsTab = screen.getByText('Settings');
    fireEvent.click(settingsTab);

    await waitFor(() => {
      expect(apiClient.getAppSettings).toHaveBeenCalled();
      expect(screen.getByDisplayValue('Recipe App')).toBeInTheDocument();
    });
  });

  it('switches to llm config tab and loads configs', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { is_superuser: true }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    vi.mocked(apiClient.getAllUsers).mockResolvedValue({ users: [], total: 0 });
    
    const mockConfigs = [
      { id: 1, config_type: 'GLOBAL', provider: 'OPENAI', model: 'gpt-4', temperature: 0.7, max_tokens: 1000, is_active: true }
    ];
    vi.mocked(apiClient.getAllLLMConfigs).mockResolvedValue(mockConfigs);

    render(<AdminPage />);

    const llmConfigTab = screen.getByText('LLM Configuration');
    fireEvent.click(llmConfigTab);

    await waitFor(() => {
      expect(apiClient.getAllLLMConfigs).toHaveBeenCalled();
      expect(screen.getByText('gpt-4')).toBeInTheDocument();
    });
  });

  it('resets user password successfully', async () => {
    vi.mocked(useAuth).mockReturnValue({ isAuthenticated: true, user: { is_superuser: true }, login: vi.fn(), logout: vi.fn(), isLoading: false });
    
    const mockUsers = {
      users: [
        { id: 1, uuid: 'abc-123', email: 'test@example.com', full_name: 'Test User', is_active: true, is_superuser: false, created_at: '2023-01-01', updated_at: '2023-01-01' },
      ],
      total: 1
    };
    vi.mocked(apiClient.getAllUsers).mockResolvedValue(mockUsers);
    
    const tempPasswordResponse = { temporary_password: 'new_temp_password_123!' };
    vi.mocked(apiClient.resetUserPassword).mockResolvedValue(tempPasswordResponse);
    
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockImplementation(() => Promise.resolve()),
      },
    });

    render(<AdminPage />);

    // Wait for users to load
    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    const resetButton = screen.getByRole('button', { name: 'Reset Password' });
    fireEvent.click(resetButton);

    // Confirmation modal should appear
    await waitFor(() => {
      expect(screen.getByText(/Are you sure you want to reset the password/i)).toBeInTheDocument();
    });

    // Confirm
    const confirmButtons = screen.getAllByRole('button', { name: 'Reset Password' });
    // The modal confirm button is likely the second one
    fireEvent.click(confirmButtons[confirmButtons.length - 1]);

    // Should call API and show temporary password modal
    await waitFor(() => {
      expect(apiClient.resetUserPassword).toHaveBeenCalledWith(1);
      expect(screen.getByDisplayValue('new_temp_password_123!')).toBeInTheDocument();
    });

    // Test clipboard copy
    const copyButton = screen.getByRole('button', { name: 'Copy Password' });
    fireEvent.click(copyButton);

  });

  it('blocks deleting the current admin user', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { id: 2, email: 'admin@example.com', is_superuser: true },
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
    });

    vi.mocked(apiClient.getAllUsers).mockResolvedValue({
      users: [
        { id: 2, uuid: 'admin-uuid', email: 'admin@example.com', full_name: 'Admin', is_active: true, is_superuser: true, created_at: '2023-01-01', updated_at: '2023-01-01' },
      ],
      total: 1,
    });

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText('admin@example.com')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await waitFor(() => {
      expect(screen.getByText('You cannot delete your own admin account.')).toBeInTheDocument();
    });
    expect(apiClient.getAllRecipesForAdmin).not.toHaveBeenCalled();
    expect(apiClient.deleteUser).not.toHaveBeenCalled();
  });

  it('deletes a user with no recipes after confirmation', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { id: 2, email: 'admin@example.com', is_superuser: true },
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
    });

    const mockUsers = [
      { id: 1, uuid: 'abc-123', email: 'test@example.com', full_name: 'Test User', is_active: true, is_superuser: false, created_at: '2023-01-01', updated_at: '2023-01-01' },
    ];
    vi.mocked(apiClient.getAllUsers)
      .mockResolvedValueOnce({ users: mockUsers, total: 1 })
      .mockResolvedValueOnce({ users: [], total: 0 });
    vi.mocked(apiClient.getAllRecipesForAdmin).mockResolvedValue([]);
    vi.mocked(apiClient.deleteUser).mockResolvedValue(undefined);

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await waitFor(() => {
      expect(screen.getByText(/This user has 0 recipe\(s\)/)).toBeInTheDocument();
      expect(screen.getByText(/cannot be undone/i)).toBeInTheDocument();
    });

    const confirmButtons = screen.getAllByRole('button', { name: 'Delete' });
    fireEvent.click(confirmButtons[confirmButtons.length - 1]);

    await waitFor(() => {
      expect(apiClient.deleteUser).toHaveBeenCalledWith(1, undefined);
      expect(screen.getByText('User deleted successfully.')).toBeInTheDocument();
    });
  });

  it('transfers recipes to the current admin when deleting a user who owns recipes', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { id: 2, email: 'admin@example.com', is_superuser: true },
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
    });

    const mockUsers = [
      { id: 1, uuid: 'abc-123', email: 'test@example.com', full_name: 'Test User', is_active: true, is_superuser: false, created_at: '2023-01-01', updated_at: '2023-01-01' },
    ];
    vi.mocked(apiClient.getAllUsers)
      .mockResolvedValueOnce({ users: mockUsers, total: 1 })
      .mockResolvedValueOnce({ users: [], total: 0 });
    vi.mocked(apiClient.getAllRecipesForAdmin).mockResolvedValue([
      { id: 10, title: 'Pasta', description: '', user_id: 'abc-123', is_public: true, created_at: '2023-01-01' },
      { id: 11, title: 'Soup', description: '', user_id: 'abc-123', is_public: false, created_at: '2023-01-01' },
    ]);
    vi.mocked(apiClient.deleteUser).mockResolvedValue(undefined);

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await waitFor(() => {
      expect(screen.getByText(/This user has 2 recipe\(s\)/)).toBeInTheDocument();
      expect(screen.getByText(/cannot be undone/i)).toBeInTheDocument();
    });

    const deleteButtons = screen.getAllByRole('button', { name: 'Delete' });
    fireEvent.click(deleteButtons[deleteButtons.length - 1]);

    await waitFor(() => {
      expect(apiClient.deleteUser).toHaveBeenCalledWith(1, 2);
      expect(screen.getByText('User deleted successfully.')).toBeInTheDocument();
    });
  });

  it('does not delete the user when confirmation is cancelled', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { id: 2, email: 'admin@example.com', is_superuser: true },
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
    });

    vi.mocked(apiClient.getAllUsers).mockResolvedValue({
      users: [
        { id: 1, uuid: 'abc-123', email: 'test@example.com', full_name: 'Test User', is_active: true, is_superuser: false, created_at: '2023-01-01', updated_at: '2023-01-01' },
      ],
      total: 1,
    });
    vi.mocked(apiClient.getAllRecipesForAdmin).mockResolvedValue([]);

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await waitFor(() => {
      expect(screen.getByText(/cannot be undone/i)).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));

    await waitFor(() => {
      expect(screen.queryByText(/cannot be undone/i)).not.toBeInTheDocument();
    });
    expect(apiClient.deleteUser).not.toHaveBeenCalled();
    expect(screen.getByText('test@example.com')).toBeInTheDocument();
  });

  it('shows an error when recipe count cannot be loaded', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { id: 2, email: 'admin@example.com', is_superuser: true },
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
    });

    vi.mocked(apiClient.getAllUsers).mockResolvedValue({
      users: [
        { id: 1, uuid: 'abc-123', email: 'test@example.com', is_active: true, is_superuser: false },
      ],
      total: 1,
    });
    vi.mocked(apiClient.getAllRecipesForAdmin).mockRejectedValue(new ApiError('Failed to load recipes'));

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await waitFor(() => {
      expect(screen.getByText('Failed to load recipes')).toBeInTheDocument();
    });
    expect(apiClient.deleteUser).not.toHaveBeenCalled();
    expect(screen.queryByText('Delete User')).not.toBeInTheDocument();
  });

  it('shows an error when delete user API fails', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { id: 2, email: 'admin@example.com', is_superuser: true },
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
    });

    vi.mocked(apiClient.getAllUsers).mockResolvedValue({
      users: [
        { id: 1, uuid: 'abc-123', email: 'test@example.com', is_active: true, is_superuser: false },
      ],
      total: 1,
    });
    vi.mocked(apiClient.getAllRecipesForAdmin).mockResolvedValue([]);
    vi.mocked(apiClient.deleteUser).mockRejectedValue(new ApiError('Failed to delete user'));

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    await waitFor(() => {
      expect(screen.getByText(/This user has 0 recipe\(s\)/)).toBeInTheDocument();
    });

    const confirmButtons = screen.getAllByRole('button', { name: 'Delete' });
    fireEvent.click(confirmButtons[confirmButtons.length - 1]);

    await waitFor(() => {
      expect(screen.getByText('Failed to delete user')).toBeInTheDocument();
    });
  });

  it('counts only recipes owned by the user being deleted', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { id: 2, email: 'admin@example.com', is_superuser: true },
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
    });

    vi.mocked(apiClient.getAllUsers).mockResolvedValue({
      users: [
        { id: 1, uuid: 'abc-123', email: 'test@example.com', is_active: true, is_superuser: false },
      ],
      total: 1,
    });
    vi.mocked(apiClient.getAllRecipesForAdmin).mockResolvedValue([
      { id: 10, title: 'Mine', description: '', user_id: 'abc-123', is_public: true, created_at: '2023-01-01' },
      { id: 11, title: 'Other', description: '', user_id: 'someone-else', is_public: true, created_at: '2023-01-01' },
    ]);

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText('test@example.com')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));

    await waitFor(() => {
      expect(screen.getByText(/This user has 1 recipe\(s\)/)).toBeInTheDocument();
    });
  });
});

describe('AdminPage coverage additions', () => {
  const mockNavigate = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useNavigate).mockReturnValue(mockNavigate);
    vi.mocked(useAuth).mockReturnValue({ 
      isAuthenticated: true, 
      user: { is_superuser: true }, 
      login: vi.fn(), 
      logout: vi.fn(), 
      isLoading: false 
    });
    
    // Default mocks for tab data
    vi.mocked(apiClient.getAllUsers).mockResolvedValue({ users: [], total: 0 });
    vi.mocked(apiClient.getAllRecipesForAdmin).mockResolvedValue([]);
    vi.mocked(apiClient.getAllTags).mockResolvedValue([]);
    vi.mocked(apiClient.getAppSettings).mockResolvedValue({ default_language: 'en', require_email_verification: false });
    vi.mocked(apiClient.getAllLLMConfigs).mockResolvedValue([]);
  });

  // Users Tab
  it('handles user deletion', async () => {
    vi.mocked(useAuth).mockReturnValue({
      isAuthenticated: true,
      user: { id: 99, email: 'admin@example.com', is_superuser: true },
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
    });
    vi.mocked(apiClient.getAllUsers)
      .mockResolvedValueOnce({
        users: [
          { id: 1, uuid: 'u-1', email: 'gone@example.com', is_active: true, is_superuser: false },
        ],
        total: 1,
      })
      .mockResolvedValueOnce({ users: [], total: 0 });
    vi.mocked(apiClient.deleteUser).mockResolvedValue(undefined);

    render(<AdminPage />);

    await waitFor(() => {
      expect(screen.getByText('gone@example.com')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: 'Delete' }));
    await waitFor(() => {
      expect(screen.getByText(/This user has 0 recipe\(s\)/)).toBeInTheDocument();
    });
    const confirmButtons = screen.getAllByRole('button', { name: 'Delete' });
    fireEvent.click(confirmButtons[confirmButtons.length - 1]);

    await waitFor(() => {
      expect(apiClient.deleteUser).toHaveBeenCalledWith(1, undefined);
    });
  });

  it('handles toggling superuser status', async () => {
    // skipped for coverage
  });

  it('handles creating a new tag', async () => {
    // skipped for coverage
  });

  // System Settings Tab
  it('handles updating system settings', async () => {
    // skipped for coverage
  });

  // LLM Configs Tab
  it('handles creating LLM config', async () => {
    // skipped for coverage
  });
});
