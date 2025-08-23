import React, { useState, useEffect, useRef, useCallback } from 'react';
import { X, Search, Plus } from 'lucide-react';
import { cn } from '../../lib/utils';
import type { Tag } from '../../lib/api-client';

export interface TagSelectorProps {
  value: Tag[];
  onChange: (tags: Tag[]) => void;
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  maxTags?: number;
  showSearch?: boolean;
  showCategories?: boolean;
  error?: string;
  className?: string;
  availableTags?: Tag[];
  onLoadTags?: () => Promise<Tag[]>;
}

// No hardcoded categories needed - we use backend data

const TagSelector: React.FC<TagSelectorProps> = ({
  value = [],
  onChange,
  placeholder = "Select tags...",
  disabled = false,
  // required = false, // Unused parameter
  maxTags,
  showSearch = true,
  showCategories = true,
  error,
  className,
  availableTags,
  onLoadTags
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [allTags, setAllTags] = useState<Tag[]>(availableTags && Array.isArray(availableTags) ? availableTags : []);
  const [loading, setLoading] = useState(false);
  const [recentTags, setRecentTags] = useState<Tag[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Load tags when input is focused for the first time
  const handleInputFocus = () => {
    console.log('Input focused. allTags length:', allTags.length, 'availableTags length:', availableTags?.length || 0);
    if (onLoadTags && allTags.length === 0) {
      console.log('Loading tags...');
      loadTags();
    }
    setIsOpen(true);
  };

  // Update allTags when availableTags prop changes
  useEffect(() => {
    // Only update if availableTags is a non-empty array
    if (availableTags && Array.isArray(availableTags) && availableTags.length > 0) {
      setAllTags(availableTags);
    }
  }, [availableTags]);

  const loadTags = async () => {
    if (!onLoadTags) return;
    
    setLoading(true);
    try {
      const tags = await onLoadTags();
      console.log('Tags loaded from API:', tags);
      console.log('Tags type:', typeof tags, 'Is array:', Array.isArray(tags));
      setAllTags(tags || []);
    } catch (error) {
      console.error('Failed to load tags:', error);
      setAllTags([]);
    } finally {
      setLoading(false);
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Focus search input when dropdown opens
  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isOpen]);

  // Filter tags based on search query and selected tags
  const filteredTags = useCallback(() => {
    // Safety check: ensure allTags is an array
    if (!Array.isArray(allTags)) {
      console.log('allTags is not an array:', allTags);
      return [];
    }
    
    console.log('Filtering tags. allTags length:', allTags.length, 'searchQuery:', searchQuery);
    console.log('allTags sample:', allTags.slice(0, 3));
    
    let filtered = allTags.filter(tag => 
      !value.some(selectedTag => selectedTag.id === tag.id) &&
      tag.name.toLowerCase().includes(searchQuery.toLowerCase())
    );

    console.log('Filtered tags:', filtered);

    // Sort by popularity (recipe_counter) and then alphabetically
    filtered.sort((a, b) => {
      if (b.recipe_counter !== a.recipe_counter) {
        return b.recipe_counter - a.recipe_counter;
      }
      return a.name.localeCompare(b.name);
    });

    return filtered;
  }, [allTags, value, searchQuery]);

  // Group tags by category using backend data
  const groupedTags = useCallback(() => {
    if (!showCategories) {
      return { 'All Tags': filteredTags() };
    }

    const grouped: Record<string, Tag[]> = {};
    const filtered = filteredTags();

    filtered.forEach(tag => {
      // Use the category from the backend
      const category = tag.category;
      
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push(tag);
    });

    return grouped;
  }, [filteredTags, showCategories]);

  const handleTagSelect = (tag: Tag) => {
    if (maxTags && value.length >= maxTags) return;
    
    const newValue = [...value, tag];
    onChange(newValue);
    setSearchQuery('');
    
    // Add to recent tags
    setRecentTags(prev => {
      const filtered = prev.filter(t => t.id !== tag.id);
      return [tag, ...filtered].slice(0, 5);
    });
  };

  const handleTagRemove = (tagToRemove: Tag) => {
    const newValue = value.filter(tag => tag.id !== tagToRemove.id);
    onChange(newValue);
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && searchQuery.trim()) {
      event.preventDefault();
      // Try to find a matching tag
      const matchingTag = filteredTags().find(tag => 
        tag.name.toLowerCase() === searchQuery.toLowerCase()
      );
      if (matchingTag) {
        handleTagSelect(matchingTag);
      }
    } else if (event.key === 'Escape') {
      setIsOpen(false);
    }
  };

  const handleSearchKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && searchQuery.trim()) {
      event.preventDefault();
      // Try to find a matching tag
      const matchingTag = filteredTags().find(tag => 
        tag.name.toLowerCase() === searchQuery.toLowerCase()
      );
      if (matchingTag) {
        handleTagSelect(matchingTag);
      }
    }
  };

  const selectedTagIds = value.map(tag => tag.id);

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Selected Tags Display */}
      <div className="min-h-[40px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50">
        <div className="flex flex-wrap gap-1">
          {value.map((tag) => (
            <TagChip
              key={tag.id}
              tag={tag}
              onRemove={() => handleTagRemove(tag)}
              disabled={disabled}
            />
          ))}
          
          {/* Input for search/dropdown trigger */}
          <div className="flex-1 min-w-[120px]">
            <input
              ref={searchInputRef}
              type="text"
              placeholder={value.length === 0 ? placeholder : "Add more tags..."}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={handleInputFocus}
              onKeyDown={handleKeyDown}
              disabled={disabled}
              className="w-full bg-transparent outline-none placeholder:text-muted-foreground"
            />
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <p className="mt-1 text-sm text-destructive">{error}</p>
      )}

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full rounded-md border bg-popover text-popover-foreground shadow-md">
          <div className="p-2">
            {/* Search Input */}
            {showSearch && (
              <div className="relative mb-2">
                <Search className="absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search tags..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleSearchKeyDown}
                  className="w-full rounded-md border bg-background px-8 py-2 text-sm outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="flex items-center justify-center py-4">
                <div 
                  className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent"
                  role="status"
                  aria-label="Loading tags"
                ></div>
              </div>
            )}

            {/* Tag List */}
            {!loading && (
              <div className="max-h-60 overflow-y-auto">
                {/* Recent Tags */}
                {recentTags.length > 0 && searchQuery === '' && (
                  <div className="mb-3">
                    <h4 className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                      Recent
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {recentTags
                        .filter(tag => !selectedTagIds.includes(tag.id))
                        .slice(0, 5)
                        .map((tag) => (
                          <TagChip
                            key={tag.id}
                            tag={tag}
                            variant="suggestion"
                            onClick={() => handleTagSelect(tag)}
                            disabled={disabled}
                          />
                        ))}
                    </div>
                  </div>
                )}

                {/* Popular Tags */}
                {searchQuery === '' && (
                  <div className="mb-3">
                    <h4 className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                      Popular
                    </h4>
                    <div className="flex flex-wrap gap-1">
                      {Array.isArray(allTags) ? allTags
                        .filter(tag => !selectedTagIds.includes(tag.id))
                        .sort((a, b) => b.recipe_counter - a.recipe_counter)
                        .slice(0, 8)
                        .map((tag) => (
                          <TagChip
                            key={tag.id}
                            tag={tag}
                            variant="suggestion"
                            onClick={() => handleTagSelect(tag)}
                            disabled={disabled}
                          />
                        )) : null}
                    </div>
                  </div>
                )}

                {/* All Tags by Category */}
                {Object.entries(groupedTags()).map(([category, tags]) => {
                  if (tags.length === 0) return null;
                  
                  return (
                    <div key={category} className="mb-3">
                      <h4 className="mb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                        {category}
                      </h4>
                      <div className="flex flex-wrap gap-1">
                        {tags.map((tag) => (
                          <TagChip
                            key={tag.id}
                            tag={tag}
                            variant="suggestion"
                            onClick={() => handleTagSelect(tag)}
                            disabled={disabled}
                          />
                        ))}
                      </div>
                    </div>
                  );
                })}

                {/* No Results */}
                {filteredTags().length === 0 && searchQuery && (
                  <div className="py-4 text-center text-sm text-muted-foreground">
                    No tags found matching "{searchQuery}"
                  </div>
                )}
              </div>
            )}

            {/* Actions */}
            <div className="mt-2 flex items-center justify-between border-t pt-2">
              <span className="text-xs text-muted-foreground">
                {value.length} selected
                {maxTags && ` / ${maxTags} max`}
              </span>
              {value.length > 0 && (
                <button
                  type="button"
                  onClick={handleClearAll}
                  className="text-xs text-muted-foreground hover:text-foreground"
                >
                  Clear all
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Tag Chip Component
interface TagChipProps {
  tag: Tag;
  variant?: 'selected' | 'suggestion';
  onRemove?: () => void;
  onClick?: () => void;
  disabled?: boolean;
}

const TagChip: React.FC<TagChipProps> = ({
  tag,
  variant = 'selected',
  onRemove,
  onClick,
  disabled = false
}) => {
  const isSelected = variant === 'selected';
  
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium transition-colors",
        isSelected
          ? "bg-primary text-primary-foreground"
          : "bg-secondary text-secondary-foreground hover:bg-secondary/80 cursor-pointer",
        disabled && "opacity-50 cursor-not-allowed"
      )}
      onClick={onClick}
    >
      <span>{tag.name}</span>
      {isSelected && onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          disabled={disabled}
          className="ml-1 rounded-full p-0.5 hover:bg-primary-foreground/20"
          aria-label={`Remove ${tag.name} tag`}
        >
          <X className="h-3 w-3" />
        </button>
      )}
      {!isSelected && (
        <Plus className="h-3 w-3" />
      )}
    </div>
  );
};

export default TagSelector;
