import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom';
import { Textarea } from '../../../src/components/ui/textarea';

describe('Textarea Component', () => {
  describe('Rendering', () => {
    it('should render with default props', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
      expect(textarea).toHaveClass('flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm');
    });

    it('should render with placeholder', () => {
      render(<Textarea placeholder="Enter text here" />);
      const textarea = screen.getByPlaceholderText('Enter text here');
      expect(textarea).toBeInTheDocument();
    });

    it('should render with custom className', () => {
      render(<Textarea className="custom-class" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('custom-class');
    });

    it('should render with value', () => {
      render(<Textarea value="test value" readOnly />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveValue('test value');
    });

    it('should render with rows attribute', () => {
      render(<Textarea rows={5} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('rows', '5');
    });

    it('should render with cols attribute', () => {
      render(<Textarea cols={50} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('cols', '50');
    });
  });

  describe('Interactions', () => {
    it('should handle change events', () => {
      const handleChange = vi.fn();
      render(<Textarea onChange={handleChange} />);
      
      const textarea = screen.getByRole('textbox');
      fireEvent.change(textarea, { target: { value: 'new text' } });
      
      expect(handleChange).toHaveBeenCalledTimes(1);
      expect(handleChange).toHaveBeenCalledWith(
        expect.objectContaining({
          target: expect.objectContaining({ value: 'new text' })
        })
      );
    });

    it('should handle focus events', () => {
      const handleFocus = vi.fn();
      render(<Textarea onFocus={handleFocus} />);
      
      const textarea = screen.getByRole('textbox');
      fireEvent.focus(textarea);
      
      expect(handleFocus).toHaveBeenCalledTimes(1);
    });

    it('should handle blur events', () => {
      const handleBlur = vi.fn();
      render(<Textarea onBlur={handleBlur} />);
      
      const textarea = screen.getByRole('textbox');
      fireEvent.blur(textarea);
      
      expect(handleBlur).toHaveBeenCalledTimes(1);
    });

    it('should handle key events', () => {
      const handleKeyDown = vi.fn();
      render(<Textarea onKeyDown={handleKeyDown} />);
      
      const textarea = screen.getByRole('textbox');
      fireEvent.keyDown(textarea, { key: 'Enter' });
      
      expect(handleKeyDown).toHaveBeenCalledTimes(1);
    });

    it('should handle input events', () => {
      const handleInput = vi.fn();
      render(<Textarea onInput={handleInput} />);
      
      const textarea = screen.getByRole('textbox');
      fireEvent.input(textarea, { target: { value: 'input text' } });
      
      expect(handleInput).toHaveBeenCalledTimes(1);
    });

    it('should be disabled when disabled prop is true', () => {
      render(<Textarea disabled />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeDisabled();
      expect(textarea).toHaveClass('disabled:cursor-not-allowed');
    });

    it('should be read-only when readOnly prop is true', () => {
      render(<Textarea readOnly />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('readonly');
    });
  });

  describe('Accessibility', () => {
    it('should have proper textbox role', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeInTheDocument();
    });

    it('should be focusable', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      textarea.focus();
      expect(textarea).toHaveFocus();
    });

    it('should have focus-visible styles', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('focus-visible:outline-none');
    });

    it('should support required attribute', () => {
      render(<Textarea required />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toBeRequired();
    });

    it('should support aria-describedby', () => {
      render(<Textarea aria-describedby="description" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-describedby', 'description');
    });

    it('should support aria-label', () => {
      render(<Textarea aria-label="Description field" />);
      const textarea = screen.getByRole('textbox', { name: /description field/i });
      expect(textarea).toBeInTheDocument();
    });

    it('should support aria-labelledby', () => {
      render(<Textarea aria-labelledby="label-id" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('aria-labelledby', 'label-id');
    });
  });

  describe('Props forwarding', () => {
    it('should forward ref', () => {
      const ref = React.createRef<HTMLTextAreaElement>();
      render(<Textarea ref={ref} />);
      expect(ref.current).toBeInstanceOf(HTMLTextAreaElement);
    });

    it('should forward data attributes', () => {
      render(<Textarea data-testid="test-textarea" />);
      const textarea = screen.getByTestId('test-textarea');
      expect(textarea).toBeInTheDocument();
    });

    it('should forward name attribute', () => {
      render(<Textarea name="description" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('name', 'description');
    });

    it('should forward id attribute', () => {
      render(<Textarea id="textarea-id" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('id', 'textarea-id');
    });

    it('should forward maxLength attribute', () => {
      render(<Textarea maxLength={100} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('maxLength', '100');
    });

    it('should forward minLength attribute', () => {
      render(<Textarea minLength={10} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('minLength', '10');
    });

    it('should forward spellCheck attribute', () => {
      render(<Textarea spellCheck={false} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('spellcheck', 'false');
    });

    it('should forward wrap attribute', () => {
      render(<Textarea wrap="hard" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveAttribute('wrap', 'hard');
    });
  });

  describe('Styling', () => {
    it('should have proper base classes', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm');
    });

    it('should have placeholder styling', () => {
      render(<Textarea placeholder="Enter text" />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('placeholder:text-muted-foreground');
    });

    it('should have focus-visible styles', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2');
    });

    it('should have disabled styles', () => {
      render(<Textarea disabled />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('disabled:cursor-not-allowed disabled:opacity-50');
    });

    it('should have ring-offset-background class', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('ring-offset-background');
    });
  });

  describe('Form Integration', () => {
    it('should work with form elements', () => {
      render(
        <form>
          <label htmlFor="description">Description</label>
          <Textarea id="description" name="description" />
        </form>
      );
      
      const textarea = screen.getByRole('textbox');
      const label = screen.getByText('Description');
      
      expect(textarea).toHaveAttribute('id', 'description');
      expect(textarea).toHaveAttribute('name', 'description');
      expect(label).toHaveAttribute('for', 'description');
    });

    it('should support form validation', () => {
      render(<Textarea required minLength={10} />);
      const textarea = screen.getByRole('textbox');
      
      expect(textarea).toBeRequired();
      expect(textarea).toHaveAttribute('minLength', '10');
    });
  });

  describe('Resize Behavior', () => {
    it('should support resize attribute', () => {
      render(<Textarea style={{ resize: 'vertical' }} />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveStyle({ resize: 'vertical' });
    });

    it('should have minimum height', () => {
      render(<Textarea />);
      const textarea = screen.getByRole('textbox');
      expect(textarea).toHaveClass('min-h-[80px]');
    });
  });
});
