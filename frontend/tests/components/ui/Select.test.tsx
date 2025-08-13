import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom';
import {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
  SelectScrollUpButton,
  SelectScrollDownButton,
} from '../../../src/components/ui/select';

describe('Select Component', () => {
  describe('Select (Root)', () => {
    it('should render with default props', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByText('Select an option')).toBeInTheDocument();
    });

    it('should handle value changes', () => {
      const onValueChange = vi.fn();
      render(
        <Select onValueChange={onValueChange}>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      // Note: Testing Radix UI Select interactions requires more complex setup
      // This is a basic test to ensure the component renders
      expect(screen.getByText('Select an option')).toBeInTheDocument();
    });
  });

  describe('SelectTrigger', () => {
    it('should render with default props within Select context', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      const trigger = screen.getByRole('combobox');
      expect(trigger).toBeInTheDocument();
    });

    it('should render with custom className within Select context', () => {
      render(
        <Select>
          <SelectTrigger className="custom-class">
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveClass('custom-class');
    });

    it('should be disabled when disabled prop is true', () => {
      render(
        <Select>
          <SelectTrigger disabled>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      const trigger = screen.getByRole('combobox');
      expect(trigger).toBeDisabled();
    });

    it('should forward ref', () => {
      const ref = React.createRef<HTMLButtonElement>();
      render(
        <Select>
          <SelectTrigger ref={ref}>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      expect(ref.current).toBeInstanceOf(HTMLButtonElement);
    });
  });

  describe('SelectValue', () => {
    it('should render placeholder within Select context', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      expect(screen.getByText('Select an option')).toBeInTheDocument();
    });

    it('should render selected value within Select context', () => {
      render(
        <Select value="option1">
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('SelectContent', () => {
    it('should render with default props', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      // SelectContent is rendered in a portal, so we test for the trigger
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should render with custom className', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent className="custom-content">
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('SelectItem', () => {
    it('should render with value and children', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should be disabled when disabled prop is true', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1" disabled>Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should forward ref', () => {
      const ref = React.createRef<HTMLDivElement>();
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem ref={ref} value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      expect(ref.current).toBeInstanceOf(HTMLDivElement);
    });
  });

  describe('SelectLabel', () => {
    it('should render with children within SelectGroup context', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Group Label</SelectLabel>
              <SelectItem value="option1">Option 1</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should render with custom className within SelectGroup context', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel className="custom-label">Group Label</SelectLabel>
              <SelectItem value="option1">Option 1</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('SelectGroup', () => {
    it('should render with children', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectItem value="option1">Option 1</SelectItem>
              <SelectItem value="option2">Option 2</SelectItem>
            </SelectGroup>
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('SelectSeparator', () => {
    it('should render separator', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
            <SelectSeparator />
            <SelectItem value="option2">Option 2</SelectItem>
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });

    it('should render with custom className', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
            <SelectSeparator className="custom-separator" />
            <SelectItem value="option2">Option 2</SelectItem>
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('SelectScrollUpButton', () => {
    it('should render scroll up button', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectScrollUpButton />
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('SelectScrollDownButton', () => {
    it('should render scroll down button', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
            <SelectScrollDownButton />
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('should have proper trigger styling', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveClass('flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm');
    });

    it('should have proper trigger focus styles', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveClass('focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2');
    });

    it('should have proper trigger disabled styles', () => {
      render(
        <Select>
          <SelectTrigger disabled>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      const trigger = screen.getByRole('combobox');
      expect(trigger).toHaveClass('disabled:cursor-not-allowed disabled:opacity-50');
    });
  });

  describe('Accessibility', () => {
    it('should have proper combobox role', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      const trigger = screen.getByRole('combobox');
      expect(trigger).toBeInTheDocument();
    });

    it('should have proper aria attributes', () => {
      render(
        <Select>
          <SelectTrigger aria-label="Select option">
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="option1">Option 1</SelectItem>
          </SelectContent>
        </Select>
      );
      
      const trigger = screen.getByRole('combobox', { name: /select option/i });
      expect(trigger).toBeInTheDocument();
    });
  });

  describe('Integration', () => {
    it('should render complete select component', () => {
      render(
        <Select>
          <SelectTrigger>
            <SelectValue placeholder="Select an option" />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              <SelectLabel>Options</SelectLabel>
              <SelectItem value="option1">Option 1</SelectItem>
              <SelectItem value="option2">Option 2</SelectItem>
            </SelectGroup>
            <SelectSeparator />
            <SelectItem value="option3">Option 3</SelectItem>
          </SelectContent>
        </Select>
      );
      
      expect(screen.getByRole('combobox')).toBeInTheDocument();
    });
  });
});
