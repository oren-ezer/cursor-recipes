import React from 'react';
import { render, screen } from '../../setup/test-utils';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import PageContainer from '../../../src/components/layout/PageContainer';

describe('PageContainer Component', () => {
  describe('Rendering', () => {
    it('should render with children', () => {
      render(
        <PageContainer>
          <div>Test content</div>
        </PageContainer>
      );
      
      expect(screen.getByText('Test content')).toBeInTheDocument();
    });

    it('should render with title', () => {
      render(
        <PageContainer title="Test Page">
          <div>Content</div>
        </PageContainer>
      );
      
      expect(screen.getByText('Test Page')).toBeInTheDocument();
      expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Test Page');
    });

    it('should render with description', () => {
      render(
        <PageContainer description="This is a test page">
          <div>Content</div>
        </PageContainer>
      );
      
      expect(screen.getByText('This is a test page')).toBeInTheDocument();
    });

    it('should render with both title and description', () => {
      render(
        <PageContainer title="Test Page" description="This is a test page">
          <div>Content</div>
        </PageContainer>
      );
      
      expect(screen.getByText('Test Page')).toBeInTheDocument();
      expect(screen.getByText('This is a test page')).toBeInTheDocument();
    });

    it('should render with custom className', () => {
      render(
        <PageContainer className="custom-class">
          <div>Content</div>
        </PageContainer>
      );
      
      const container = screen.getByText('Content').closest('.custom-class');
      expect(container).toBeInTheDocument();
    });
  });

  describe('Conditional Rendering', () => {
    it('should not render header section when no title or description', () => {
      render(
        <PageContainer>
          <div>Content</div>
        </PageContainer>
      );
      
      // Should not have the header div with mb-6 class
      const headerSection = screen.getByText('Content').parentElement?.parentElement;
      expect(headerSection).not.toHaveClass('mb-6');
    });

    it('should render header section when title is provided', () => {
      render(
        <PageContainer title="Test Page">
          <div>Content</div>
        </PageContainer>
      );
      
      const headerSection = screen.getByText('Test Page').closest('.mb-6');
      expect(headerSection).toBeInTheDocument();
    });

    it('should render header section when description is provided', () => {
      render(
        <PageContainer description="Test description">
          <div>Content</div>
        </PageContainer>
      );
      
      const headerSection = screen.getByText('Test description').closest('.mb-6');
      expect(headerSection).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('should have proper base container classes', () => {
      render(
        <PageContainer>
          <div>Content</div>
        </PageContainer>
      );
      
      const container = screen.getByText('Content').closest('.px-4.py-6');
      expect(container).toHaveClass('px-4 py-6 sm:px-0 bg-white dark:bg-gray-800 shadow rounded-lg');
    });

    it('should have proper title styling', () => {
      render(
        <PageContainer title="Test Page">
          <div>Content</div>
        </PageContainer>
      );
      
      const title = screen.getByText('Test Page');
      expect(title).toHaveClass('text-3xl font-bold text-gray-900 dark:text-gray-100');
    });

    it('should have proper description styling', () => {
      render(
        <PageContainer description="Test description">
          <div>Content</div>
        </PageContainer>
      );
      
      const description = screen.getByText('Test description');
      expect(description).toHaveClass('mt-2 text-lg text-gray-600 dark:text-gray-300');
    });

    it('should have proper content container styling', () => {
      render(
        <PageContainer>
          <div>Content</div>
        </PageContainer>
      );
      
      const contentContainer = screen.getByText('Content').parentElement;
      expect(contentContainer).toHaveClass('px-4 sm:px-6');
    });
  });

  describe('Dark Mode Support', () => {
    it('should have dark mode classes', () => {
      render(
        <PageContainer>
          <div>Content</div>
        </PageContainer>
      );
      
      const container = screen.getByText('Content').closest('.bg-white');
      expect(container).toHaveClass('dark:bg-gray-800');
    });

    it('should have dark mode title classes', () => {
      render(
        <PageContainer title="Test Page">
          <div>Content</div>
        </PageContainer>
      );
      
      const title = screen.getByText('Test Page');
      expect(title).toHaveClass('dark:text-gray-100');
    });

    it('should have dark mode description classes', () => {
      render(
        <PageContainer description="Test description">
          <div>Content</div>
        </PageContainer>
      );
      
      const description = screen.getByText('Test description');
      expect(description).toHaveClass('dark:text-gray-300');
    });
  });

  describe('Responsive Design', () => {
    it('should have responsive padding classes', () => {
      render(
        <PageContainer>
          <div>Content</div>
        </PageContainer>
      );
      
      const container = screen.getByText('Content').closest('.px-4.py-6');
      expect(container).toHaveClass('sm:px-0');
    });

    it('should have responsive header padding', () => {
      render(
        <PageContainer title="Test Page">
          <div>Content</div>
        </PageContainer>
      );
      
      const headerSection = screen.getByText('Test Page').closest('.px-4');
      expect(headerSection).toHaveClass('sm:px-6');
    });

    it('should have responsive content padding', () => {
      render(
        <PageContainer>
          <div>Content</div>
        </PageContainer>
      );
      
      const contentContainer = screen.getByText('Content').parentElement;
      expect(contentContainer).toHaveClass('sm:px-6');
    });
  });

  describe('Accessibility', () => {
    it('should have proper heading structure', () => {
      render(
        <PageContainer title="Test Page">
          <div>Content</div>
        </PageContainer>
      );
      
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toBeInTheDocument();
      expect(heading).toHaveTextContent('Test Page');
    });

    it('should have proper semantic structure', () => {
      render(
        <PageContainer title="Test Page" description="Test description">
          <div>Content</div>
        </PageContainer>
      );
      
      const heading = screen.getByRole('heading', { level: 1 });
      const description = screen.getByText('Test description');
      
      expect(heading).toBeInTheDocument();
      expect(description).toBeInTheDocument();
    });
  });

  describe('Props forwarding', () => {
    it('should forward custom className', () => {
      render(
        <PageContainer className="test-class">
          <div>Content</div>
        </PageContainer>
      );
      
      const container = screen.getByText('Content').closest('.test-class');
      expect(container).toBeInTheDocument();
    });

    it('should combine custom className with default classes', () => {
      render(
        <PageContainer className="test-class">
          <div>Content</div>
        </PageContainer>
      );
      
      const container = screen.getByText('Content').closest('.test-class');
      expect(container).toHaveClass('px-4 py-6 sm:px-0 bg-white dark:bg-gray-800 shadow rounded-lg test-class');
    });
  });
});
