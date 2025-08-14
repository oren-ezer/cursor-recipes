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
    register: vi.fn(),
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
import RegisterPage from '../../src/pages/RegisterPage';
import { useAuth } from '../../src/contexts/AuthContext';
import { apiClient } from '../../src/lib/api-client';
import { useNavigate } from 'react-router-dom';

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

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    
    // Setup default mocks
    vi.mocked(useAuth).mockReturnValue(createMockAuth());
    vi.mocked(useNavigate).mockReturnValue(vi.fn());
    vi.mocked(apiClient.register).mockResolvedValue(undefined);
  });

  describe('Rendering', () => {
    it('should render registration form with all elements', () => {
      renderWithRouter(<RegisterPage />);
      
      expect(screen.getAllByText('Create an Account')).toHaveLength(1);
      expect(screen.getByText('Enter your details below to create your account')).toBeInTheDocument();
      
      // Form fields
      expect(screen.getByLabelText('Email')).toBeInTheDocument();
      expect(screen.getByLabelText('Full Name (Optional)')).toBeInTheDocument();
      expect(screen.getByLabelText('Password')).toBeInTheDocument();
      expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument();
      
      // Submit button
      expect(screen.getByRole('button', { name: 'Create Account' })).toBeInTheDocument();
      
      // Links
      expect(screen.getByRole('link', { name: 'Login here' })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Go to Home' })).toBeInTheDocument();
    });

    it('should render form with correct input types and placeholders', () => {
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const fullNameInput = screen.getByLabelText('Full Name (Optional)');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      
      expect(emailInput).toHaveAttribute('type', 'email');
      expect(emailInput).toHaveAttribute('placeholder', 'm@example.com');
      expect(emailInput).toHaveAttribute('required');
      
      expect(fullNameInput).toHaveAttribute('type', 'text');
      expect(fullNameInput).toHaveAttribute('placeholder', 'John Doe');
      expect(fullNameInput).not.toHaveAttribute('required');
      
      expect(passwordInput).toHaveAttribute('type', 'password');
      expect(passwordInput).toHaveAttribute('required');
      
      expect(confirmPasswordInput).toHaveAttribute('type', 'password');
      expect(confirmPasswordInput).toHaveAttribute('required');
    });
  });

  describe('Form Interaction', () => {
    it('should update form fields when user types', () => {
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const fullNameInput = screen.getByLabelText('Full Name (Optional)');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(fullNameInput, { target: { value: 'John Doe' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      
      expect(emailInput).toHaveValue('test@example.com');
      expect(fullNameInput).toHaveValue('John Doe');
      expect(passwordInput).toHaveValue('password123');
      expect(confirmPasswordInput).toHaveValue('password123');
    });

    it('should clear error when user starts typing', () => {
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      
      // First, trigger an error by submitting empty form
      const submitButton = screen.getByRole('button', { name: 'Create Account' });
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
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const fullNameInput = screen.getByLabelText('Full Name (Optional)');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(fullNameInput, { target: { value: 'John Doe' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.register)).toHaveBeenCalledWith('test@example.com', 'password123', 'John Doe');
      });
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login', {
          state: {
            message: 'Registration successful! Please log in with your new account.'
          }
        });
      });
    });

    it('should submit form without full name when not provided', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.register)).toHaveBeenCalledWith('test@example.com', 'password123', undefined);
      });
    });

    it('should show loading state during submission', async () => {
      // Make the API call take some time
      vi.mocked(apiClient.register).mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(undefined), 100)));
      
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      // Should show loading state
      expect(screen.getByRole('button', { name: 'Creating Account...' })).toBeInTheDocument();
      expect(emailInput).toBeDisabled();
      expect(passwordInput).toBeDisabled();
      expect(confirmPasswordInput).toBeDisabled();
    });

    it('should handle form submission via enter key', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      
      // Submit form by pressing enter in confirm password field
      fireEvent.keyDown(confirmPasswordInput, { key: 'Enter', code: 'Enter', charCode: 13 });
      
      // Alternative: submit the form directly
      const form = confirmPasswordInput.closest('form');
      if (form) {
        fireEvent.submit(form);
      }
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.register)).toHaveBeenCalledWith('test@example.com', 'password123', undefined);
      });
    });
  });

  describe('Form Validation', () => {
    it('should show error when required fields are empty', async () => {
      renderWithRouter(<RegisterPage />);
      
      const form = screen.getByRole('button', { name: 'Create Account' }).closest('form');
      fireEvent.submit(form!);
      
      await waitFor(() => {
        expect(screen.getByText('All fields are required')).toBeInTheDocument();
      });
    });

    it('should show error when passwords do not match', async () => {
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const form = screen.getByRole('button', { name: 'Create Account' }).closest('form');
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'differentpassword' } });
      fireEvent.submit(form!);
      
      await waitFor(() => {
        expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
      });
    });

    it('should show error when password is too short', async () => {
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const form = screen.getByRole('button', { name: 'Create Account' }).closest('form');
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: '123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: '123' } });
      fireEvent.submit(form!);
      
      await waitFor(() => {
        expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
      });
    });

    it('should show error when email format is invalid', async () => {
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const form = screen.getByRole('button', { name: 'Create Account' }).closest('form');
      
      fireEvent.change(emailInput, { target: { value: 'invalid-email' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.submit(form!);
      
      await waitFor(() => {
        expect(screen.getByText('Please enter a valid email address')).toBeInTheDocument();
      });
    });

    it('should require email field', () => {
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      expect(emailInput).toHaveAttribute('required');
    });

    it('should require password field', () => {
      renderWithRouter(<RegisterPage />);
      
      const passwordInput = screen.getByLabelText('Password');
      expect(passwordInput).toHaveAttribute('required');
    });

    it('should require confirm password field', () => {
      renderWithRouter(<RegisterPage />);
      
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      expect(confirmPasswordInput).toHaveAttribute('required');
    });

    it('should validate email format', () => {
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      expect(emailInput).toHaveAttribute('type', 'email');
    });
  });

  describe('Error Handling', () => {
    it('should display ApiError message', async () => {
      // Import ApiError directly to ensure proper instanceof check
      const { ApiError } = await import('../../src/lib/api-client');
      const apiError = new ApiError('Email already exists');
      vi.mocked(apiClient.register).mockRejectedValue(apiError);
      
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('Email already exists')).toBeInTheDocument();
      });
    });

    it('should display generic error for unexpected errors', async () => {
      vi.mocked(apiClient.register).mockRejectedValue(new Error('Network error'));
      
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('An unexpected error occurred')).toBeInTheDocument();
      });
    });

    it('should clear error when form is resubmitted', async () => {
      // First call fails, second call succeeds
      vi.mocked(apiClient.register)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(undefined);
      
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      
      // First submission - should fail
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('An unexpected error occurred')).toBeInTheDocument();
      });
      
      // Second submission - should succeed
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.queryByText('An unexpected error occurred')).not.toBeInTheDocument();
      });
      
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/login', {
          state: {
            message: 'Registration successful! Please log in with your new account.'
          }
        });
      });
    });
  });

  describe('Navigation', () => {
    it('should navigate to login page when login link is clicked', () => {
      renderWithRouter(<RegisterPage />);
      
      const loginLink = screen.getByRole('link', { name: 'Login here' });
      expect(loginLink).toHaveAttribute('href', '/login');
    });

    it('should navigate to home page when home link is clicked', () => {
      renderWithRouter(<RegisterPage />);
      
      const homeLink = screen.getByRole('link', { name: 'Go to Home' });
      expect(homeLink).toHaveAttribute('href', '/');
    });
  });

  describe('Loading State Management', () => {
    it('should disable form inputs during loading', async () => {
      // Make the API call take some time
      vi.mocked(apiClient.register).mockImplementation(() => new Promise(resolve => setTimeout(() => resolve(undefined), 100)));
      
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const fullNameInput = screen.getByLabelText('Full Name (Optional)');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      // Should disable inputs during loading
      expect(emailInput).toBeDisabled();
      expect(fullNameInput).toBeDisabled();
      expect(passwordInput).toBeDisabled();
      expect(confirmPasswordInput).toBeDisabled();
      expect(submitButton).toBeDisabled();
    });

    it('should re-enable form inputs after error', async () => {
      vi.mocked(apiClient.register).mockRejectedValue(new Error('Network error'));
      
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const fullNameInput = screen.getByLabelText('Full Name (Optional)');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(screen.getByText('An unexpected error occurred')).toBeInTheDocument();
      });
      
      // Should re-enable inputs after error
      expect(emailInput).not.toBeDisabled();
      expect(fullNameInput).not.toBeDisabled();
      expect(passwordInput).not.toBeDisabled();
      expect(confirmPasswordInput).not.toBeDisabled();
      expect(submitButton).not.toBeDisabled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty form submission', async () => {
      renderWithRouter(<RegisterPage />);
      
      const form = screen.getByRole('button', { name: 'Create Account' }).closest('form');
      fireEvent.submit(form!);
      
      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText('All fields are required')).toBeInTheDocument();
      });
    });

    it('should handle rapid form submissions', async () => {
      const mockNavigate = vi.fn();
      vi.mocked(useNavigate).mockReturnValue(mockNavigate);
      
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      
      fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      
      // Click submit multiple times rapidly
      fireEvent.click(submitButton);
      fireEvent.click(submitButton);
      fireEvent.click(submitButton);
      
      // Should only call API once
      await waitFor(() => {
        expect(vi.mocked(apiClient.register)).toHaveBeenCalledTimes(1);
      });
    });

    it('should handle whitespace in email', async () => {
      renderWithRouter(<RegisterPage />);
      
      const emailInput = screen.getByLabelText('Email');
      const passwordInput = screen.getByLabelText('Password');
      const confirmPasswordInput = screen.getByLabelText('Confirm Password');
      const submitButton = screen.getByRole('button', { name: 'Create Account' });
      
      fireEvent.change(emailInput, { target: { value: '  test@example.com  ' } });
      fireEvent.change(passwordInput, { target: { value: 'password123' } });
      fireEvent.change(confirmPasswordInput, { target: { value: 'password123' } });
      fireEvent.click(submitButton);
      
      await waitFor(() => {
        expect(vi.mocked(apiClient.register)).toHaveBeenCalledWith('test@example.com', 'password123', undefined);
      });
    });
  });
});
