import React, { useState } from 'react';
import TagSelector from '../components/ui/tag-selector';
import { apiClient } from '../lib/api-client';
import type { Tag } from '../lib/api-client';

const TagSelectorDemo: React.FC = () => {
  const [selectedTags, setSelectedTags] = useState<Tag[]>([]);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [loading, setLoading] = useState(false);
  const [tagsLoaded, setTagsLoaded] = useState(false);

  const loadTags = async (): Promise<Tag[]> => {
    try {
      console.log('Calling apiClient.getAllTags()...');
      const tags = await apiClient.getAllTags();
      console.log(`Loaded ${tags.length} tags from backend:`, tags);
      console.log('Tags type:', typeof tags, 'Is array:', Array.isArray(tags));
      setAvailableTags(tags);
      setTagsLoaded(true);
      return tags;
    } catch (error) {
      console.error('Failed to load tags:', error);
      return [];
    }
  };

  const handleLoadTags = async () => {
    setLoading(true);
    await loadTags();
    setLoading(false);
  };

  return (
    <div className="container mx-auto p-6 max-w-2xl">
      <h1 className="text-3xl font-bold mb-6">Tag Selector Demo</h1>
      
      <div className="space-y-6">
        {/* Load Tags Button */}
        <div>
          <button
            onClick={handleLoadTags}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Load Tags'}
          </button>
          {tagsLoaded && (
            <span className="ml-2 text-sm text-gray-600">
              {availableTags.length} tags loaded successfully
            </span>
          )}
        </div>

        {/* Tag Selector */}
        <div>
          <label className="block text-sm font-medium mb-2">Select Tags</label>
          <TagSelector
            value={selectedTags}
            onChange={setSelectedTags}
            placeholder="Choose tags for your recipe..."
            availableTags={availableTags}
            onLoadTags={loadTags}
            maxTags={10}
            showSearch={true}
            showCategories={true}
          />
        </div>

        {/* Selected Tags Display */}
        <div>
          <h3 className="text-lg font-semibold mb-2">Selected Tags:</h3>
          {selectedTags.length === 0 ? (
            <p className="text-gray-500">No tags selected</p>
          ) : (
            <div className="space-y-2">
              {selectedTags.map((tag) => (
                <div key={tag.id} className="flex items-center justify-between p-2 bg-gray-100 rounded">
                  <span className="font-medium">{tag.name}</span>
                  <span className="text-sm text-gray-600">
                    Used in {tag.recipe_counter} recipes
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* JSON Output */}
        <div>
          <h3 className="text-lg font-semibold mb-2">Selected Tags (JSON):</h3>
          <pre className="bg-gray-100 p-4 rounded text-sm overflow-auto">
            {JSON.stringify(selectedTags, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default TagSelectorDemo;
