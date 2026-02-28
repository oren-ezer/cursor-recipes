# AI Tag Suggestion Integration - Implementation Plan

## Overview
Integrate AI-powered tag suggestions into the recipe creation and editing flow to help users quickly and accurately tag their recipes based on the recipe title and ingredients.

## Current State Analysis

### Existing Components
1. **Backend**: `/api/v1/ai/suggest-tags` endpoint already exists
   - Input: `recipe_title`, `ingredients[]`, `existing_tags[]` (optional)
   - Output: `suggested_tags[]` (tag names), `confidence` score
2. **Frontend**: `TagSelector` component in recipe forms
   - Used in both `RecipeCreatePage` and `RecipeEditPage`
   - Has search, categories, popular tags, and recent tags
3. **API Client**: `apiClient.suggestTags()` method already exists

### What's Missing
- UI integration: No way to trigger AI suggestions from the recipe form
- User feedback: Loading states, error handling for AI suggestions
- Tag matching: Backend returns tag names, need to match with existing Tag objects
- Translations: No i18n keys for AI suggestion feature

---

## Implementation Plan

### Phase 1: Backend Changes (Minimal)

#### 1.1 Verify/Enhance Tag Suggestion Endpoint
**File**: `backend/src/api/v1/endpoints/ai.py`

**Current Status**: ✅ Endpoint exists and is functional

**Potential Enhancement** (Optional):
- Return full tag objects instead of just names to avoid frontend matching complexity
- Add `tag_id` alongside `tag_name` in response

**Action**: 
```python
# Optional enhancement to TagSuggestionResponse
class TagSuggestionResponse(BaseModel):
    suggested_tags: List[Dict[str, Any]]  # [{id: 1, name: "Italian"}, ...]
    confidence: float
```

**Decision**: Keep current implementation (tag names only) to maintain simplicity and allow for suggestions of tags that don't exist yet.

---

### Phase 2: Frontend API Integration

#### 2.1 Update API Client Types
**File**: `frontend/src/lib/api-client.ts`

**Status**: ✅ Already has `suggestTags` method

**Verify**:
```typescript
async suggestTags(data: TagSuggestionRequest): Promise<TagSuggestionResponse> {
  return this.request<TagSuggestionResponse>('/ai/suggest-tags', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}
```

**Action**: No changes needed

---

### Phase 3: TagSelector Component Enhancement

#### 3.1 Add AI Suggestion Feature to TagSelector
**File**: `frontend/src/components/ui/tag-selector.tsx`

**Changes**:

1. **Add new props**:
```typescript
export interface TagSelectorProps {
  // ... existing props
  onSuggestTags?: () => Promise<string[]>;  // Callback to get AI suggestions
  showAiSuggestion?: boolean;  // Enable/disable AI feature
}
```

2. **Add state variables**:
```typescript
const [aiSuggestions, setAiSuggestions] = useState<Tag[]>([]);
const [isLoadingAi, setIsLoadingAi] = useState(false);
const [aiError, setAiError] = useState<string | null>(null);
```

3. **Add suggestion handler**:
```typescript
const handleGetAiSuggestions = async () => {
  if (!onSuggestTags) return;
  
  setIsLoadingAi(true);
  setAiError(null);
  setAiSuggestions([]);
  
  try {
    const suggestedTagNames = await onSuggestTags();
    
    // Match suggested names with available tags
    const matchedTags = suggestedTagNames
      .map(name => allTags.find(tag => 
        tag.name.toLowerCase() === name.toLowerCase()
      ))
      .filter((tag): tag is Tag => tag !== undefined);
    
    setAiSuggestions(matchedTags);
  } catch (error) {
    console.error('AI suggestion error:', error);
    setAiError(t('tag_selector.ai_error'));
  } finally {
    setIsLoadingAi(false);
  }
};
```

4. **Add UI for AI suggestions**:
```typescript
{/* AI Suggestions Button - in dropdown header */}
{showAiSuggestion && onSuggestTags && (
  <button
    type="button"
    onClick={handleGetAiSuggestions}
    disabled={isLoadingAi || loading}
    className="mb-2 w-full rounded-md bg-gradient-to-r from-purple-500 to-indigo-600 px-3 py-2 text-sm font-medium text-white hover:from-purple-600 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
  >
    {isLoadingAi ? (
      <>
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
        <span>{t('tag_selector.ai_loading')}</span>
      </>
    ) : (
      <>
        <Sparkles className="h-4 w-4" />
        <span>{t('tag_selector.ai_suggest')}</span>
      </>
    )}
  </button>
)}

{/* AI Suggestions Display - after search input, before popular tags */}
{aiSuggestions.length > 0 && (
  <div className="mb-3 rounded-md bg-gradient-to-r from-purple-50 to-indigo-50 dark:from-purple-900/20 dark:to-indigo-900/20 p-3 border border-purple-200 dark:border-purple-800">
    <div className="flex items-center gap-2 mb-2">
      <Sparkles className="h-4 w-4 text-purple-600 dark:text-purple-400" />
      <h4 className="text-xs font-semibold text-purple-700 dark:text-purple-300 uppercase tracking-wide">
        {t('tag_selector.ai_suggestions')} ({Math.round(confidence * 100)}% {t('tag_selector.confidence')})
      </h4>
    </div>
    <div className="flex flex-wrap gap-1">
      {aiSuggestions
        .filter(tag => !selectedTagIds.includes(tag.id))
        .map((tag) => (
          <TagChip
            key={tag.id}
            tag={tag}
            variant="ai-suggestion"
            onClick={() => {
              handleTagSelect(tag);
              // Remove from suggestions after selection
              setAiSuggestions(prev => prev.filter(t => t.id !== tag.id));
            }}
            disabled={disabled}
          />
        ))}
    </div>
    <button
      type="button"
      onClick={() => {
        // Add all AI suggestions at once
        const newTags = aiSuggestions.filter(tag => !selectedTagIds.includes(tag.id));
        onChange([...value, ...newTags]);
        setAiSuggestions([]);
      }}
      className="mt-2 text-xs text-purple-700 dark:text-purple-300 hover:text-purple-900 dark:hover:text-purple-100 underline"
    >
      {t('tag_selector.add_all_suggestions')}
    </button>
  </div>
)}

{/* AI Error Display */}
{aiError && (
  <div className="mb-2 rounded-md bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 px-3 py-2 text-sm text-red-800 dark:text-red-200">
    {aiError}
  </div>
)}
```

5. **Update TagChip for AI suggestions**:
```typescript
const TagChip: React.FC<TagChipProps> = ({
  tag,
  variant = 'selected',
  // ...
}) => {
  const isAiSuggestion = variant === 'ai-suggestion';
  
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium transition-colors",
        isSelected && "bg-primary text-primary-foreground",
        variant === 'suggestion' && "bg-secondary text-secondary-foreground hover:bg-secondary/80 cursor-pointer",
        isAiSuggestion && "bg-gradient-to-r from-purple-500 to-indigo-600 text-white hover:from-purple-600 hover:to-indigo-700 cursor-pointer",
        disabled && "opacity-50 cursor-not-allowed"
      )}
      onClick={onClick}
    >
      {isAiSuggestion && <Sparkles className="h-3 w-3" />}
      <span>{tag.name}</span>
      {/* ... rest of component */}
    </div>
  );
};
```

6. **Add imports**:
```typescript
import { X, Search, Plus, Sparkles } from 'lucide-react';
```

---

### Phase 4: Recipe Form Integration

#### 4.1 Update RecipeCreatePage
**File**: `frontend/src/pages/RecipeCreatePage.tsx`

**Changes**:

1. **Add state for AI confidence**:
```typescript
const [aiSuggestionConfidence, setAiSuggestionConfidence] = useState<number>(0);
```

2. **Create suggestion handler**:
```typescript
const handleAiTagSuggestion = async (): Promise<string[]> => {
  // Only suggest if we have title and at least one ingredient
  if (!formData.title.trim() || formData.ingredients.every(ing => !ing.name.trim())) {
    throw new Error(t('recipe.form.ai_suggestion_requirements'));
  }

  try {
    const ingredientsList = formData.ingredients
      .filter(ing => ing.name.trim())
      .map(ing => ing.name);
    
    const response = await apiClient.suggestTags({
      recipe_title: formData.title,
      ingredients: ingredientsList,
      existing_tags: formData.selectedTags.map(tag => tag.name),
    });

    setAiSuggestionConfidence(response.confidence);
    return response.suggested_tags;
  } catch (error) {
    console.error('Failed to get AI suggestions:', error);
    throw error;
  }
};
```

3. **Update TagSelector usage**:
```tsx
<TagSelector
  value={formData.selectedTags}
  onChange={handleTagsChange}
  placeholder={t('recipe.form.tags_placeholder')}
  disabled={isLoading}
  onLoadTags={loadTagsWithLogging}
  showSearch={true}
  showCategories={true}
  showAiSuggestion={true}  // NEW
  onSuggestTags={handleAiTagSuggestion}  // NEW
/>
```

4. **Update help text to mention AI**:
```tsx
<p className="text-sm text-gray-600 dark:text-gray-400">
  {t('recipe.form.tags_help_with_ai')}
</p>
```

#### 4.2 Update RecipeEditPage
**File**: `frontend/src/pages/RecipeEditPage.tsx`

**Changes**: Same as RecipeCreatePage (steps 1-4 above)

---

### Phase 5: Translations

#### 5.1 Add Translation Keys
**File**: `frontend/src/i18n/translations.ts`

**English**:
```typescript
// Tag Selector - AI Suggestions
"tag_selector.ai_suggest": "✨ Suggest Tags with AI",
"tag_selector.ai_loading": "Getting suggestions...",
"tag_selector.ai_suggestions": "AI Suggested Tags",
"tag_selector.confidence": "confidence",
"tag_selector.ai_error": "Failed to get AI suggestions. Please try again.",
"tag_selector.add_all_suggestions": "Add all suggestions",

// Recipe Form - AI
"recipe.form.tags_help_with_ai": "Add tags to help others discover your recipe. You can search by name, browse by category, or use AI to suggest relevant tags based on your recipe title and ingredients.",
"recipe.form.ai_suggestion_requirements": "Please add a recipe title and at least one ingredient to get AI tag suggestions.",
```

**Hebrew**:
```typescript
// Tag Selector - AI Suggestions
"tag_selector.ai_suggest": "✨ הצע תגיות באמצעות AI",
"tag_selector.ai_loading": "מקבל הצעות...",
"tag_selector.ai_suggestions": "תגיות מוצעות על ידי AI",
"tag_selector.confidence": "ביטחון",
"tag_selector.ai_error": "נכשל בקבלת הצעות AI. אנא נסה שוב.",
"tag_selector.add_all_suggestions": "הוסף את כל ההצעות",

// Recipe Form - AI
"recipe.form.tags_help_with_ai": "הוסף תגיות כדי לעזור לאחרים לגלות את המתכון שלך. תוכל לחפש לפי שם, לעיין לפי קטגוריה, או להשתמש ב-AI כדי להציע תגיות רלוונטיות בהתבסס על כותרת המתכון והמרכיבים.",
"recipe.form.ai_suggestion_requirements": "אנא הוסף כותרת מתכון ולפחות מרכיב אחד כדי לקבל הצעות תגיות מ-AI.",
```

---

### Phase 6: Testing

#### 6.1 Backend Tests
**File**: `backend/tests/api/v1/test_ai_endpoints.py`

**Verify existing tests**:
- Test tag suggestion with valid recipe data
- Test with minimal data (title + 1 ingredient)
- Test with existing tags
- Test error handling

#### 6.2 Frontend Tests (Optional)
**File**: `frontend/tests/components/TagSelector.test.tsx`

**New tests to add**:
1. AI suggestion button renders when `showAiSuggestion` is true
2. AI suggestion button is disabled during loading
3. Successfully displays AI suggestions
4. Handles AI suggestion errors gracefully
5. Can add individual AI suggestions
6. Can add all AI suggestions at once
7. AI suggestions are removed after selection

---

## UX Considerations

### 1. When to Show AI Suggestions
- ✅ Only enable AI button after user has entered:
  - Recipe title (non-empty)
  - At least one ingredient name
- ✅ Show inline validation message if requirements not met

### 2. Visual Design
- Use purple/indigo gradient to distinguish AI suggestions from regular tags
- Add sparkle icon (✨) to indicate AI-powered feature
- Show confidence score as percentage
- Smooth animations for loading states

### 3. Performance
- AI calls are on-demand (button click), not automatic
- Use debouncing if we implement auto-suggestions in future
- Cache suggestions during the form session

### 4. Error Handling
- Network errors: "Failed to get suggestions, try again"
- Validation errors: "Please add title and ingredients first"
- No matching tags: Show suggestions even if not in database (for admin to add later)

### 5. Accessibility
- Proper ARIA labels for AI button
- Keyboard navigation support
- Screen reader announcements for loading/success/error states

---

## Implementation Checklist

### Backend
- [ ] Verify `/api/v1/ai/suggest-tags` endpoint works correctly
- [ ] Test with various recipe inputs
- [ ] Verify error handling

### Frontend - TagSelector Component
- [ ] Add `showAiSuggestion` and `onSuggestTags` props
- [ ] Add state variables (suggestions, loading, error)
- [ ] Implement `handleGetAiSuggestions` function
- [ ] Add AI suggestion button UI
- [ ] Add AI suggestions display section with confidence score
- [ ] Add "Add all" functionality
- [ ] Update TagChip to support `ai-suggestion` variant
- [ ] Add Sparkles icon import
- [ ] Add error display UI

### Frontend - Recipe Forms
- [ ] Add AI confidence state to RecipeCreatePage
- [ ] Implement `handleAiTagSuggestion` in RecipeCreatePage
- [ ] Update TagSelector usage in RecipeCreatePage
- [ ] Add AI confidence state to RecipeEditPage
- [ ] Implement `handleAiTagSuggestion` in RecipeEditPage
- [ ] Update TagSelector usage in RecipeEditPage
- [ ] Update help text in both forms

### Translations
- [ ] Add English translations for AI features
- [ ] Add Hebrew translations for AI features
- [ ] Verify RTL support for Hebrew

### Testing
- [ ] Manual testing: Create recipe with AI suggestions
- [ ] Manual testing: Edit recipe with AI suggestions
- [ ] Manual testing: Error scenarios (no title, no ingredients)
- [ ] Manual testing: Network error handling
- [ ] Verify confidence score display
- [ ] Verify "Add all" functionality
- [ ] Test on mobile/tablet layouts

### Documentation
- [ ] Update user guide with AI tag suggestion feature
- [ ] Add screenshots/GIFs of feature in action
- [ ] Document any API rate limiting considerations

---

## Estimated Effort

- **Backend**: 0-1 hour (verification only)
- **Frontend - TagSelector**: 3-4 hours
- **Frontend - Recipe Forms**: 1-2 hours
- **Translations**: 30 minutes
- **Testing**: 2-3 hours
- **Documentation**: 1 hour

**Total**: ~8-12 hours

---

## Future Enhancements

1. **Auto-suggest on form change**: Automatically suggest tags when title/ingredients change (with debouncing)
2. **Learn from user selections**: Track which AI suggestions users accept/reject
3. **Batch processing**: Suggest tags for existing recipes without tags
4. **Admin review**: Flag AI-suggested tags that don't exist in the database
5. **Multi-language support**: Train AI on Hebrew recipes for better suggestions
6. **Confidence threshold**: Allow users to set minimum confidence level
7. **Explanation**: Show why AI suggested each tag (e.g., "Based on ingredient: tomatoes")

---

## Risk Mitigation

### Risk: AI service unavailable or slow
**Mitigation**: 
- Timeout after 10 seconds
- Clear error message with fallback to manual tag selection
- Don't block form submission if AI fails

### Risk: Poor quality suggestions
**Mitigation**:
- Show confidence score
- Allow manual override
- Track feedback for model improvement

### Risk: Cost concerns (API usage)
**Mitigation**:
- On-demand only (not automatic)
- Cache results per session
- Monitor usage in admin dashboard
- Set rate limits if needed

---

## Success Metrics

1. **Adoption Rate**: % of recipes using AI suggestions
2. **Acceptance Rate**: % of AI suggestions actually added to recipes
3. **Time Saved**: Average time to tag a recipe (before/after)
4. **Tag Quality**: Increase in appropriate tags per recipe
5. **User Satisfaction**: Feedback/ratings on the AI feature

---

## Rollout Plan

### Phase 1: Soft Launch (Week 1)
- Deploy to production
- Announce in admin dashboard
- Monitor for errors/performance issues

### Phase 2: User Education (Week 2)
- Add tooltip/hint on first use
- Blog post or email about new feature
- Collect initial feedback

### Phase 3: Optimization (Week 3-4)
- Analyze metrics
- Fine-tune confidence thresholds
- Implement user feedback

### Phase 4: Scale (Month 2+)
- Consider auto-suggestions
- Expand to other languages
- Add advanced features

