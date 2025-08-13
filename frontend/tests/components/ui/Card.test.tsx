import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter 
} from '../../../src/components/ui/card';

describe('Card Component', () => {
  describe('Card', () => {
    it('should render with default props', () => {
      render(<Card>Card content</Card>);
      const card = screen.getByText('Card content');
      expect(card).toBeInTheDocument();
      expect(card).toHaveClass('rounded-xl border bg-card text-card-foreground shadow');
    });

    it('should render with custom className', () => {
      render(<Card className="custom-class">Custom Card</Card>);
      const card = screen.getByText('Custom Card');
      expect(card).toHaveClass('custom-class');
    });

    it('should forward ref', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(<Card ref={ref}>Ref Card</Card>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });

    it('should forward data attributes', () => {
      render(<Card data-testid="test-card">Data Card</Card>);
      const card = screen.getByTestId('test-card');
      expect(card).toBeInTheDocument();
    });
  });

  describe('CardHeader', () => {
    it('should render with default props', () => {
      render(<CardHeader>Header content</CardHeader>);
      const header = screen.getByText('Header content');
      expect(header).toBeInTheDocument();
      expect(header).toHaveClass('flex flex-col space-y-1.5 p-6');
    });

    it('should render with custom className', () => {
      render(<CardHeader className="custom-header">Custom Header</CardHeader>);
      const header = screen.getByText('Custom Header');
      expect(header).toHaveClass('custom-header');
    });

    it('should forward ref', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(<CardHeader ref={ref}>Ref Header</CardHeader>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe('CardTitle', () => {
    it('should render with default props', () => {
      render(<CardTitle>Card Title</CardTitle>);
      const title = screen.getByText('Card Title');
      expect(title).toBeInTheDocument();
      expect(title).toHaveClass('font-semibold leading-none tracking-tight');
    });

    it('should render with custom className', () => {
      render(<CardTitle className="custom-title">Custom Title</CardTitle>);
      const title = screen.getByText('Custom Title');
      expect(title).toHaveClass('custom-title');
    });

    it('should forward ref', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(<CardTitle ref={ref}>Ref Title</CardTitle>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe('CardDescription', () => {
    it('should render with default props', () => {
      render(<CardDescription>Card Description</CardDescription>);
      const description = screen.getByText('Card Description');
      expect(description).toBeInTheDocument();
      expect(description).toHaveClass('text-sm text-muted-foreground');
    });

    it('should render with custom className', () => {
      render(<CardDescription className="custom-desc">Custom Description</CardDescription>);
      const description = screen.getByText('Custom Description');
      expect(description).toHaveClass('custom-desc');
    });

    it('should forward ref', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(<CardDescription ref={ref}>Ref Description</CardDescription>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe('CardContent', () => {
    it('should render with default props', () => {
      render(<CardContent>Content</CardContent>);
      const content = screen.getByText('Content');
      expect(content).toBeInTheDocument();
      expect(content).toHaveClass('p-6 pt-0');
    });

    it('should render with custom className', () => {
      render(<CardContent className="custom-content">Custom Content</CardContent>);
      const content = screen.getByText('Custom Content');
      expect(content).toHaveClass('custom-content');
    });

    it('should forward ref', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(<CardContent ref={ref}>Ref Content</CardContent>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe('CardFooter', () => {
    it('should render with default props', () => {
      render(<CardFooter>Footer</CardFooter>);
      const footer = screen.getByText('Footer');
      expect(footer).toBeInTheDocument();
      expect(footer).toHaveClass('flex items-center p-6 pt-0');
    });

    it('should render with custom className', () => {
      render(<CardFooter className="custom-footer">Custom Footer</CardFooter>);
      const footer = screen.getByText('Custom Footer');
      expect(footer).toHaveClass('custom-footer');
    });

    it('should forward ref', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(<CardFooter ref={ref}>Ref Footer</CardFooter>);
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe('Card Composition', () => {
    it('should render complete card structure', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Recipe Title</CardTitle>
            <CardDescription>Recipe description</CardDescription>
          </CardHeader>
          <CardContent>
            <p>Recipe content goes here</p>
          </CardContent>
          <CardFooter>
            <button>Action</button>
          </CardFooter>
        </Card>
      );

      expect(screen.getByText('Recipe Title')).toBeInTheDocument();
      expect(screen.getByText('Recipe description')).toBeInTheDocument();
      expect(screen.getByText('Recipe content goes here')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /action/i })).toBeInTheDocument();
    });

    it('should render card with only header and content', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Simple Card</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Simple content</p>
          </CardContent>
        </Card>
      );

      expect(screen.getByText('Simple Card')).toBeInTheDocument();
      expect(screen.getByText('Simple content')).toBeInTheDocument();
    });

    it('should render card with only content', () => {
      render(
        <Card>
          <CardContent>
            <p>Content only</p>
          </CardContent>
        </Card>
      );

      expect(screen.getByText('Content only')).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper semantic structure', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Accessible Card</CardTitle>
          </CardHeader>
          <CardContent>
            <p>Accessible content</p>
          </CardContent>
        </Card>
      );

      const card = screen.getByText('Accessible Card').closest('div');
      expect(card).toBeInTheDocument();
    });

    it('should support ARIA attributes', () => {
      render(
        <Card aria-label="Recipe card">
          <CardContent>Content</CardContent>
        </Card>
      );

      const card = screen.getByLabelText('Recipe card');
      expect(card).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('should have proper base card styling', () => {
      render(<Card>Styled Card</Card>);
      const card = screen.getByText('Styled Card');
      expect(card).toHaveClass('rounded-xl border bg-card text-card-foreground shadow');
    });

    it('should have proper header styling', () => {
      render(<CardHeader>Styled Header</CardHeader>);
      const header = screen.getByText('Styled Header');
      expect(header).toHaveClass('flex flex-col space-y-1.5 p-6');
    });

    it('should have proper title styling', () => {
      render(<CardTitle>Styled Title</CardTitle>);
      const title = screen.getByText('Styled Title');
      expect(title).toHaveClass('font-semibold leading-none tracking-tight');
    });

    it('should have proper description styling', () => {
      render(<CardDescription>Styled Description</CardDescription>);
      const description = screen.getByText('Styled Description');
      expect(description).toHaveClass('text-sm text-muted-foreground');
    });

    it('should have proper content styling', () => {
      render(<CardContent>Styled Content</CardContent>);
      const content = screen.getByText('Styled Content');
      expect(content).toHaveClass('p-6 pt-0');
    });

    it('should have proper footer styling', () => {
      render(<CardFooter>Styled Footer</CardFooter>);
      const footer = screen.getByText('Styled Footer');
      expect(footer).toHaveClass('flex items-center p-6 pt-0');
    });
  });
});
