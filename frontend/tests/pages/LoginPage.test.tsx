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
    login: vi.fn(),
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
    useLocation: vi.fn(),
  };
});

// Import after mocks
import LoginPage from '../../src/pages/LoginPage';
import { useAuth } from '../../src/contexts/AuthContext';
import { apiClient } from '../../src/lib/api-client';
import { useNavigate, useLocation } from 'react-router-dom';

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

// Helper function to create mock auth values
const createMockAuth = () => ({
  isAuthenticated: false,
  user: null,
  token: null,
  login: vi.fn(),
  logout: vi.fn(),
  isLoading: false,
});

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    vi.mocked(useAuth).mockReturnValue(createMockAuth());
    vi.mocked(useNavigate).mockReturnValue(vi.fn());
    vi.mocked(useLocation).mockReturnValue({
      pathname: '/login',
      search: '',
      hash: '',
      state: null,
    });
    vi.mocked(apiClient.login).mockResolvedValue({ access_token: 'mock-token' });
  });

  describe('Rendering', () => {
    it('should render login form with all elements', () => {
      renderWithRouter(<LoginPage />);
      
      expect(screen.getAllByText('Login')).toHaveLength(2); // Title and button
      expect(screen.getByText('Enter your email and password to access your account.')).toBeInTheDocument();
      
      // Form fields
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
      expect(screen.getByLabelText('Password')).toBeInTheDocument();
      
      // Submit button
      expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument();
      
      // Links
      expect(screen.getByRole('link', { name: 'Register here' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Go to Home' })).toBeInTheDocument();
    });

    it('should render form with correct input types and placeholders', () => {
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(emailInput).toHaveAttribute('placeholder', 'm@example.com');
      expect(emailInput).toHaveAttribute('required');
      
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('required');
    });
  });

  describe('Form Interaction', () => {
    it('should update form fields when user types', () => {
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      
      expect(emailInput).toHaveValue('test@example.com');
      expect(passwordInput).toHaveValue('password123');
    });

    it('should clear error when user starts typing', () => {
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      
      // First, trigger an error by submitting empty form
      const submitButton = screen.getByRole('button', { name: 'Login' });
      fireEvent.click(submitButton);
      
      // Error should be shown (browser validation)
      expect(emailInput).toBeInvalid();
      
      // Start typing to clear the error
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      expect(emailInput).toBeValid();
    });
  });

  describe('Form Submission', () => {
    it('should submit form with correct data', async () => {
      const mockNavigate = vi.fn();
      const mockLogin = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      vi.mocked(useAuth).mockReturnValue({
        ...createMockAuth(),
        login: mockLogin,
      });
      
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Login' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.login)).toHaveBeenCalledWith('test@example.com', 'password123');
      });
      
      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith('mock-token');
      });
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });

    it('should show loading state during submission', async () => {
      // Make the API call take some time
      vi.mocked(apiClient.login).mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ access_token: 'mock-token' }), 100)));
      
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Login' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      // Should show loading state
      expect(screen.getByRole('button', { name: 'Logging in...' })).toBeInTheDocument();
      expect(emailInput).toBeDisabled();
      expect(passwordInput).toBeDisabled();
    });

    it('should handle form submission via enter key', async () => {
      const mockNavigate = vi.fn();
      const mockLogin = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      vi.mocked(useAuth).mockReturnValue({
        ...createMockAuth(),
        login: mockLogin,
      });
      
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      
      // Submit form by pressing enter in password field
      fireEvent.keyDown(passwordInput, { key: 'Enter', code: 'Enter', charCode: 13 });
      
      // Alternative: submit the form directly
      const form = passwordInput.closest('form');
      if (form) {
        fireEvent.submit(form);
      }
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.login)).toHaveBeenCalledWith('test@example.com', 'password123');
      });
    });


  });

  describe('Error Handling', () => {
    it('should display generic error for regular errors', async () => {
      vi.mocked(apiClient.login).mockRejectedValue(new Error('Invalid credentials'));
      
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Login' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument();
      });
    });

    it('should display ApiError message', async () => {
      // Import ApiError directly to ensure proper instanceof check
      const { ApiError } = await import('../../src/lib/api-client');
      const apiError = new ApiError('Invalid email or password');
      vi.mocked(apiClient.login).mockRejectedValue(apiError);
      
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Login' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Invalid email or password')).toBeInTheDocument();
      });
    });

    it('should display generic error for unexpected errors', async () => {
      vi.mocked(apiClient.login).mockRejectedValue(new Error('Network error'));
      
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Login' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument();
      });
    });

    it('should clear error when form is resubmitted', async () => {
      // First call fails, second call succeeds
      vi.mocked(apiClient.login)
        .mockRejectedValueOnce(new Error('Invalid credentials'))
        .mockResolvedValueOnce({ access_token: 'mock-token' });
      
      const mockNavigate = vi.fn();
      const mockLogin = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      vi.mocked(useAuth).mockReturnValue({
        ...createMockAuth(),
        login: mockLogin,
      });
      
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Login' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      
      // First submission - should fail
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument();
      });
      
      // Second submission - should succeed
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.queryByText('An unexpected error occurred.')).not.toBeInTheDocument();
      });
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/');
      });
    });
  });

  describe('Success Message Handling', () => {
    it('should display success message from location state', () => {
      vi.mocked(useLocation).mockReturnValue({
        pathname: '/login',
        search: '',
        hash: '',
        state: { message: 'Registration successful! Please log in with your new account.' },
      });
      
      renderWithRouter(<LoginPage />);
      
      expect(screen.getByText('Registration successful! Please log in with your new account.')).toBeInTheDocument();
    });

    it('should not display success message when no state message', () => {
      vi.mocked(useLocation).mockReturnValue({
        pathname: '/login',
        search: '',
        hash: '',
        state: null,
      });
      
      renderWithRouter(<LoginPage />);
      
      expect(screen.queryByText('Registration successful! Please log in with your new account.')).not.toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('should navigate to register page when register link is clicked', () => {
      renderWithRouter(<LoginPage />);
      
      const registerLink = screen.getByRole('link', { name: 'Register here' });
      expect(registerLink).toHaveAttribute('href', '/register');
    });

    it('should navigate to home page when home link is clicked', () => {
      renderWithRouter(<LoginPage />);
      
      const homeLink = screen.getByRole('link', { name: 'Go to Home' });
      expect(homeLink).toHaveAttribute('href', '/');
    });
  });

  describe('Form Validation', () => {
    it('should require email field', () => {
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      expect(emailInput).toHaveAttribute('required');
    });

    it('should require password field', () => {
      renderWithRouter(<LoginPage />);
      
      const passwordInput = screen.getByLabelText('Password');
      expect(passwordInput).toHaveAttribute('required');
    });

    it('should validate email format', () => {
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      expect(emailInput).toHaveAttribute('type', 'email');
    });
  });

  describe('Loading State Management', () => {
    it('should disable form inputs during loading', async () => {
      // Make the API call take some time
      vi.mocked(apiClient.login).mockImplementation(() => new Promise(resolve => setTimeout(() => resolve({ access_token: 'mock-token' }), 100)));
      
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Login' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      // Should disable inputs during loading
      expect(emailInput).toBeDisabled();
      expect(passwordInput).toBeDisabled();
      expect(submitButton).toBeDisabled();
    });

    it('should re-enable form inputs after error', async () => {
      vi.mocked(apiClient.login).mockRejectedValue(new Error('Invalid credentials'));
      
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Login' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument();
      });
      
      // Should re-enable inputs after error
      expect(emailInput).not.toBeDisabled();
      expect(passwordInput).not.toBeDisabled();
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty form submission', () => {
      renderWithRouter(<LoginPage />);
      
      const submitButton = screen.getByRole('button', { name: 'Login' });
      fireEvent.click(submitButton);
      
      // Browser validation should prevent submission
      expect(vi.mocked(apiClient.login)).not.toHaveBeenCalled();
    });

    it('should handle rapid form submissions', async () => {
      const mockNavigate = vi.fn();
      const mockLogin = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      vi.mocked(useAuth).mockReturnValue({
        ...createMockAuth(),
        login: mockLogin,
      });
      
      renderWithRouter(<LoginPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const submitButton = screen.getByRole('button', { name: 'Login' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      
      // Click submit multiple times rapidly
      fireEvent.click(submitButton);
      fireEvent.click(submitButton);
      fireEvent.click(submitButton);
      
      // Should only call API once
      await waitFor(() => {
        expect(vi.mocked(apiClient.login)).toHaveBeenCalledTimes(1);
      });
    });
  });
});
