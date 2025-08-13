import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom';
import { BrowserRouter } from 'react-router-dom';
import MainLayout from '../../../src/components/layout/MainLayout';
import { AuthProvider } from '../../../src/contexts/AuthProvider';

// Mock the useAuth hook
const mockUseAuth = vi.fn();

vi.mock('../../../src/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('MainLayout Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render with children', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        logout: vi.fn(),
      });

      renderWithRouter(
        <MainLayout>
          <div>Test content</div>
        </MainLayout>
      );

      expect(screen.getByText('Test content')).toBeInTheDocument();
    });

    it('should render navigation header', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        logout: vi.fn(),
      });

      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      expect(screen.getByText('Recipe App')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /home/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /about/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /recipes/i })).toBeInTheDocument();
    });
  });

  describe('Navigation Links', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        logout: vi.fn(),
      });
    });

    it('should render all navigation links', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const homeLink = screen.getByRole('link', { name: /home/i });
      const aboutLink = screen.getByRole('link', { name: /about/i });
      const recipesLink = screen.getByRole('link', { name: /recipes/i });

      expect(homeLink).toHaveAttribute('href', '/');
      expect(aboutLink).toHaveAttribute('href', '/about');
      expect(recipesLink).toHaveAttribute('href', '/recipes');
    });

    it('should render app logo as link to home', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const logoLink = screen.getByRole('link', { name: /recipe app/i });
      expect(logoLink).toHaveAttribute('href', '/');
    });
  });

  describe('Unauthenticated State', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        logout: vi.fn(),
      });
    });

    it('should show login and register links when not authenticated', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      expect(screen.getByRole('link', { name: /login/i })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /register/i })).toBeInTheDocument();
    });

    it('should not show authenticated-only links', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      expect(screen.queryByRole('link', { name: /my recipes/i })).not.toBeInTheDocument();
      expect(screen.queryByText(/@/)).not.toBeInTheDocument(); // Email display
      expect(screen.queryByRole('button', { name: /logout/i })).not.toBeInTheDocument();
    });

    it('should have correct login link', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const loginLink = screen.getByRole('link', { name: /login/i });
      expect(loginLink).toHaveAttribute('href', '/login');
    });

    it('should have correct register link', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const registerLink = screen.getByRole('link', { name: /register/i });
      expect(registerLink).toHaveAttribute('href', '/register');
    });
  });

  describe('Authenticated State', () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      full_name: 'Test User',
    };

    const mockLogout = vi.fn();

    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        user: mockUser,
        logout: mockLogout,
      });
    });

    it('should show user email and logout button when authenticated', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      expect(screen.getByText('test@example.com')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /logout/i })).toBeInTheDocument();
    });

    it('should show My Recipes link when authenticated', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const myRecipesLink = screen.getByRole('link', { name: /my recipes/i });
      expect(myRecipesLink).toBeInTheDocument();
      expect(myRecipesLink).toHaveAttribute('href', '/my-recipes');
    });

    it('should not show login and register links when authenticated', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      expect(screen.queryByRole('link', { name: /login/i })).not.toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /register/i })).not.toBeInTheDocument();
    });

    it('should call logout function when logout button is clicked', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const logoutButton = screen.getByRole('button', { name: /logout/i });
      fireEvent.click(logoutButton);

      expect(mockLogout).toHaveBeenCalledTimes(1);
    });
  });

  describe('Styling and Classes', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        logout: vi.fn(),
      });
    });

    it('should have proper container classes', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const container = screen.getByText('Content').closest('.min-h-screen');
      expect(container).toHaveClass('min-h-screen bg-gray-100 dark:bg-gray-900');
    });

    it('should have proper navigation classes', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const nav = screen.getByText('Recipe App').closest('nav');
      expect(nav).toHaveClass('bg-white dark:bg-gray-800 shadow-md');
    });

    it('should have proper main content classes', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const main = screen.getByText('Content').closest('main');
      expect(main).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        logout: vi.fn(),
      });
    });

    it('should have proper navigation structure', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const nav = screen.getByText('Recipe App').closest('nav');
      expect(nav).toBeInTheDocument();
    });

    it('should have proper link roles', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const links = screen.getAllByRole('link');
      expect(links.length).toBeGreaterThan(0);
      
      links.forEach(link => {
        expect(link).toHaveAttribute('href');
      });
    });

    it('should have proper button roles', () => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: true,
        user: { email: 'test@example.com' },
        logout: vi.fn(),
      });

      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const logoutButton = screen.getByRole('button', { name: /logout/i });
      expect(logoutButton).toBeInTheDocument();
    });
  });

  describe('Responsive Design', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        logout: vi.fn(),
      });
    });

    it('should have responsive container classes', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const container = screen.getByText('Content').closest('.max-w-7xl');
      expect(container).toHaveClass('max-w-7xl mx-auto py-6 sm:px-6 lg:px-8');
    });

    it('should have responsive navigation classes', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const navContainer = screen.getByText('Recipe App').closest('.max-w-7xl');
      expect(navContainer).toHaveClass('max-w-7xl mx-auto px-4 sm:px-6 lg:px-8');
    });
  });

  describe('Dark Mode Support', () => {
    beforeEach(() => {
      mockUseAuth.mockReturnValue({
        isAuthenticated: false,
        user: null,
        logout: vi.fn(),
      });
    });

    it('should have dark mode classes', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const container = screen.getByText('Content').closest('.min-h-screen');
      expect(container).toHaveClass('dark:bg-gray-900');
    });

    it('should have dark mode navigation classes', () => {
      renderWithRouter(
        <MainLayout>
          <div>Content</div>
        </MainLayout>
      );

      const nav = screen.getByText('Recipe App').closest('nav');
      expect(nav).toHaveClass('dark:bg-gray-800');
    });
  });
});
