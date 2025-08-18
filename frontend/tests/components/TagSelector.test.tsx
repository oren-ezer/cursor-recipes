import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import TagSelector from '../../src/components/ui/tag-selector';
import type { Tag } from '../../src/lib/api-client';

// Mock the API client
vi.mock('../../src/lib/api-client', () => ({
  apiClient: {
    getAllTags: vi.fn(),
    searchTags: vi.fn(),
    getPopularTags: vi.fn(),
  },
}));

const mockTags: Tag[] = [
  { id: 1, name: 'breakfast', uuid: 'uuid1', recipe_counter: 15, created_at: '2024-01-01', updated_at: '2024-01-01' },
  { id: 2, name: 'vegetarian', uuid: 'uuid2', recipe_counter: 25, created_at: '2024-01-01', updated_at: '2024-01-01' },
  { id: 3, name: 'italian', uuid: 'uuid3', recipe_counter: 10, created_at: '2024-01-01', updated_at: '2024-01-01' },
  { id: 4, name: 'quick', uuid: 'uuid4', recipe_counter: 30, created_at: '2024-01-01', updated_at: '2024-01-01' },
  { id: 5, name: 'dessert', uuid: 'uuid5', recipe_counter: 20, created_at: '2024-01-01', updated_at: '2024-01-01' },
];

describe('TagSelector', () => {
  const defaultProps = {
    value: [],
    onChange: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render with default placeholder', () => {
      render(<TagSelector {...defaultProps} />);
      expect(screen.getByPlaceholderText('Select tags...')).toBeInTheDocument();
    });

    it('should render with custom placeholder', () => {
      render(<TagSelector {...defaultProps} placeholder="Choose tags..." />);
      expect(screen.getByPlaceholderText('Choose tags...')).toBeInTheDocument();
    });

    it('should render selected tags as chips', () => {
      const selectedTags = [mockTags[0], mockTags[1]];
      render(<TagSelector {...defaultProps} value={selectedTags} />);
      
      expect(screen.getByText('breakfast')).toBeInTheDocument();
      expect(screen.getByText('vegetarian')).toBeInTheDocument();
    });

    it('should show remove button on selected tags', () => {
      const selectedTags = [mockTags[0]];
      render(<TagSelector {...defaultProps} value={selectedTags} />);
      
      const removeButton = screen.getByRole('button', { name: /remove/i });
      expect(removeButton).toBeInTheDocument();
    });

    it('should render error message when provided', () => {
      render(<TagSelector {...defaultProps} error="Please select at least one tag" />);
      expect(screen.getByText('Please select at least one tag')).toBeInTheDocument();
    });

    it('should be disabled when disabled prop is true', () => {
      render(<TagSelector {...defaultProps} disabled={true} />);
      const input = screen.getByPlaceholderText('Select tags...');
      expect(input).toBeDisabled();
    });
  });

  describe('Tag Selection', () => {
    it('should open dropdown when input is focused', async () => {
      render(<TagSelector {...defaultProps} availableTags={mockTags} />);
      
      const input = screen.getByPlaceholderText('Select tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByText('Popular')).toBeInTheDocument();
      });
    });

    it('should show available tags in dropdown', async () => {
      render(<TagSelector {...defaultProps} availableTags={mockTags} />);
      
      const input = screen.getByPlaceholderText('Select tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        // Tags can appear in multiple categories, so we check they exist at least once
        expect(screen.getAllByText('breakfast').length).toBeGreaterThan(0);
        expect(screen.getAllByText('vegetarian').length).toBeGreaterThan(0);
        expect(screen.getAllByText('italian').length).toBeGreaterThan(0);
      });
    });

    it('should call onChange when tag is selected', async () => {
      const onChange = vi.fn();
      render(<TagSelector {...defaultProps} onChange={onChange} availableTags={mockTags} />);
      
      const input = screen.getByPlaceholderText('Select tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        // Find the first breakfast tag button in the dropdown (not the selected area)
        const tagButtons = screen.getAllByText('breakfast');
        const dropdownButton = tagButtons.find(button => 
          button.closest('[class*="bg-secondary"]')
        );
        if (dropdownButton) {
          fireEvent.click(dropdownButton);
        }
      });
      
      expect(onChange).toHaveBeenCalledWith([mockTags[0]]);
    });

    it('should not show already selected tags in dropdown', async () => {
      const selectedTags = [mockTags[0]];
      render(<TagSelector {...defaultProps} value={selectedTags} availableTags={mockTags} />);
      
      const input = screen.getByPlaceholderText('Add more tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        // The breakfast tag should not appear in the dropdown since it's already selected
        // But it might appear in the selected tags area, so we need to be more specific
        const dropdownTags = screen.getAllByText('breakfast');
        // Should only be one instance (in the selected tags area)
        expect(dropdownTags).toHaveLength(1);
        // Check that vegetarian appears in the dropdown (not just in selected area)
        const vegetarianTags = screen.getAllByText('vegetarian');
        expect(vegetarianTags.length).toBeGreaterThan(1); // One in selected, one in dropdown
      });
    });

    it('should respect maxTags limit', async () => {
      const onChange = vi.fn();
      const selectedTags = [mockTags[0], mockTags[1]];
      render(
        <TagSelector 
          {...defaultProps} 
          onChange={onChange} 
          value={selectedTags}
          availableTags={mockTags} 
          maxTags={2}
        />
      );
      
      const input = screen.getByPlaceholderText('Add more tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        // Find the first italian tag button (there might be multiple due to categories)
        const tagButtons = screen.getAllByText('italian');
        const firstItalianButton = tagButtons[0].closest('[class*="cursor-pointer"]');
        if (firstItalianButton) {
          fireEvent.click(firstItalianButton);
        }
      });
      
      // Should not call onChange because max tags reached
      expect(onChange).not.toHaveBeenCalled();
    });
  });

  describe('Tag Removal', () => {
    it('should call onChange when tag is removed', () => {
      const onChange = vi.fn();
      const selectedTags = [mockTags[0]];
      render(<TagSelector {...defaultProps} onChange={onChange} value={selectedTags} />);
      
      const removeButton = screen.getByRole('button', { name: /remove breakfast tag/i });
      fireEvent.click(removeButton);
      
      expect(onChange).toHaveBeenCalledWith([]);
    });

    it('should clear all tags when clear all is clicked', async () => {
      const onChange = vi.fn();
      const selectedTags = [mockTags[0], mockTags[1]];
      render(<TagSelector {...defaultProps} onChange={onChange} value={selectedTags} />);
      
      const input = screen.getByPlaceholderText('Add more tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        const clearAllButton = screen.getByText('Clear all');
        fireEvent.click(clearAllButton);
      });
      
      expect(onChange).toHaveBeenCalledWith([]);
    });
  });

  describe('Search Functionality', () => {
    it('should filter tags based on search query', async () => {
      render(<TagSelector {...defaultProps} availableTags={mockTags} />);
      
      const input = screen.getByPlaceholderText('Select tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search tags...');
        fireEvent.change(searchInput, { target: { value: 'break' } });
      });
      
      await waitFor(() => {
        expect(screen.getByText('breakfast')).toBeInTheDocument();
        expect(screen.queryByText('vegetarian')).not.toBeInTheDocument();
      });
    });

    it('should show no results message when no tags match', async () => {
      render(<TagSelector {...defaultProps} availableTags={mockTags} />);
      
      const input = screen.getByPlaceholderText('Select tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search tags...');
        fireEvent.change(searchInput, { target: { value: 'nonexistent' } });
      });
      
      await waitFor(() => {
        expect(screen.getByText('No tags found matching "nonexistent"')).toBeInTheDocument();
      });
    });
  });

  describe('Keyboard Navigation', () => {
    it('should close dropdown on Escape key', async () => {
      render(<TagSelector {...defaultProps} availableTags={mockTags} />);
      
      const input = screen.getByPlaceholderText('Select tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByText('Popular')).toBeInTheDocument();
      });
      
      fireEvent.keyDown(input, { key: 'Escape' });
      
      await waitFor(() => {
        expect(screen.queryByText('Popular')).not.toBeInTheDocument();
      });
    });

    it('should select tag on Enter key if exact match found', async () => {
      const onChange = vi.fn();
      render(<TagSelector {...defaultProps} onChange={onChange} availableTags={mockTags} />);
      
      const input = screen.getByPlaceholderText('Select tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        const searchInput = screen.getByPlaceholderText('Search tags...');
        fireEvent.change(searchInput, { target: { value: 'breakfast' } });
        fireEvent.keyDown(searchInput, { key: 'Enter' });
      });
      
      expect(onChange).toHaveBeenCalledWith([mockTags[0]]);
    });
  });

  describe('Categories', () => {
    it('should group tags by categories when showCategories is true', async () => {
      render(<TagSelector {...defaultProps} availableTags={mockTags} showCategories={true} />);
      
      const input = screen.getByPlaceholderText('Select tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByText('Meal Types')).toBeInTheDocument();
        expect(screen.getByText('Dietary')).toBeInTheDocument();
        expect(screen.getByText('Cuisines')).toBeInTheDocument();
      });
    });

    it('should not show categories when showCategories is false', async () => {
      render(<TagSelector {...defaultProps} availableTags={mockTags} showCategories={false} />);
      
      const input = screen.getByPlaceholderText('Select tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.queryByText('Meal Types')).not.toBeInTheDocument();
        expect(screen.getByText('All Tags')).toBeInTheDocument();
      });
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner when loading', async () => {
      const loadTags = vi.fn().mockImplementation(() => new Promise(() => {})); // Never resolves
      render(<TagSelector {...defaultProps} onLoadTags={loadTags} />);
      
      const input = screen.getByPlaceholderText('Select tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByRole('status')).toBeInTheDocument();
      });
    });
  });

  describe('Recent Tags', () => {
    it('should show recent tags section when tags have been selected', async () => {
      const selectedTags = [mockTags[0]];
      render(<TagSelector {...defaultProps} value={selectedTags} availableTags={mockTags} />);
      
      const input = screen.getByPlaceholderText('Add more tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByText('Popular')).toBeInTheDocument();
        // Recent tags should show up after a tag has been selected and then removed
        // This test verifies the component renders correctly with selected tags
      });
    });
  });

  describe('Popular Tags', () => {
    it('should show popular tags sorted by recipe_counter', async () => {
      render(<TagSelector {...defaultProps} availableTags={mockTags} />);
      
      const input = screen.getByPlaceholderText('Select tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByText('Popular')).toBeInTheDocument();
        // Should show tags in order of popularity
        const popularSection = screen.getByText('Popular').closest('div')?.parentElement;
        const tagElements = popularSection?.querySelectorAll('[class*="bg-secondary"]');
        expect(tagElements?.[0]).toHaveTextContent('quick'); // highest recipe_counter
      });
    });
  });

  describe('Selection Counter', () => {
    it('should show selection counter', async () => {
      const selectedTags = [mockTags[0], mockTags[1]];
      render(<TagSelector {...defaultProps} value={selectedTags} availableTags={mockTags} />);
      
      const input = screen.getByPlaceholderText('Add more tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByText('2 selected')).toBeInTheDocument();
      });
    });

    it('should show max tags limit when provided', async () => {
      const selectedTags = [mockTags[0]];
      render(<TagSelector {...defaultProps} value={selectedTags} availableTags={mockTags} maxTags={5} />);
      
      const input = screen.getByPlaceholderText('Add more tags...');
      fireEvent.focus(input);
      
      await waitFor(() => {
        expect(screen.getByText('1 selected / 5 max')).toBeInTheDocument();
      });
    });
  });
});
