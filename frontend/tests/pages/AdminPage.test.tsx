import React from 'react';
import { screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import { render, fireEvent } from '../setup/test-utils';
import AdminPage from '../../src/pages/AdminPage';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../src/contexts/AuthContext';
import { apiClient } from '../../src/lib/api-client';

vi.mock('../../src/lib/api-client', () => ({
  apiClient: {
    getAllUsers: vi.fn(),
    getAllRecipesForAdmin: vi.fn(),
    getAllTags: vi.fn(),
    getAppSettings: vi.fn(),
    getAllLLMConfigs: vi.fn(),
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
});
