import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import { Label } from '../../../src/components/ui/label';

describe('Label Component', () => {
  describe('Rendering', () => {
    it('should render with default props', () => {
      render(<Label>Test Label</Label>);
      const label = screen.getByText('Test Label');
      expect(label).toBeInTheDocument();
      expect(label).toHaveClass('text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70');
    });

    it('should render with custom className', () => {
      render(<Label className="custom-class">Custom Label</Label>);
      const label = screen.getByText('Custom Label');
      expect(label).toHaveClass('custom-class');
    });

    it('should render with htmlFor attribute', () => {
      render(<Label htmlFor="test-input">Input Label</Label>);
      const label = screen.getByText('Input Label');
      // Radix UI Label might use 'for' instead of 'htmlFor'
      expect(label).toHaveAttribute('for', 'test-input');
    });
  });

  describe('Props forwarding', () => {
    it('should forward ref', () => {
      const ref = React.createRef<HTMLLabelElement>();
      render(<Label ref={ref}>Ref Label</Label>);
      expect(ref.current).toBeInstanceOf(HTMLLabelElement);
    });

    it('should forward data attributes', () => {
      render(<Label data-testid="test-label">Data Label</Label>);
      const label = screen.getByTestId('test-label');
      expect(label).toBeInTheDocument();
    });

    it('should forward id attribute', () => {
      render(<Label id="label-id">ID Label</Label>);
      const label = screen.getByText('ID Label');
      expect(label).toHaveAttribute('id', 'label-id');
    });
  });

  describe('Accessibility', () => {
    it('should have proper label role', () => {
      render(<Label>Accessible Label</Label>);
      const label = screen.getByText('Accessible Label');
      expect(label.tagName).toBe('LABEL');
    });

    it('should support aria-describedby', () => {
      render(<Label aria-describedby="description">Aria Label</Label>);
      const label = screen.getByText('Aria Label');
      expect(label).toHaveAttribute('aria-describedby', 'description');
    });

    it('should support aria-label', () => {
      render(<Label aria-label="Screen reader label">Visible Label</Label>);
      const label = screen.getByLabelText('Screen reader label');
      expect(label).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('should have proper base classes', () => {
      render(<Label>Styled Label</Label>);
      const label = screen.getByText('Styled Label');
      expect(label).toHaveClass('text-sm font-medium leading-none');
    });

    it('should have peer disabled styles', () => {
      render(<Label>Peer Label</Label>);
      const label = screen.getByText('Peer Label');
      expect(label).toHaveClass('peer-disabled:cursor-not-allowed peer-disabled:opacity-70');
    });
  });

  describe('Integration with form elements', () => {
    it('should work with input elements', () => {
      render(
        <div>
          <Label htmlFor="test-input">Input Label</Label>
          <input id="test-input" />
        </div>
      );
      
      const label = screen.getByText('Input Label');
      const input = screen.getByRole('textbox');
      
      expect(label).toHaveAttribute('for', 'test-input');
      expect(input).toHaveAttribute('id', 'test-input');
    });

    it('should work with textarea elements', () => {
      render(
        <div>
          <Label htmlFor="test-textarea">Textarea Label</Label>
          <textarea id="test-textarea" />
        </div>
      );
      
      const label = screen.getByText('Textarea Label');
      const textarea = screen.getByRole('textbox');
      
      expect(label).toHaveAttribute('for', 'test-textarea');
      expect(textarea).toHaveAttribute('id', 'test-textarea');
    });
  });
});
