import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { apiClient, ApiError } from '../lib/api-client';
import type { Tag, User, Recipe } from '../lib/api-client';
import MainLayout from '../components/layout/MainLayout';
import PageContainer from '../components/layout/PageContainer';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import ConfirmationModal from '../components/ui/confirmation-modal';

const AdminPage: React.FC = () => {
  const { isAuthenticated, user } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<'users' | 'recipes' | 'tags' | 'system'>('users');
  
  // Tags state
  const [tags, setTags] = useState<Tag[]>([]);
  const [isCreating, setIsCreating] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagCategory, setNewTagCategory] = useState('');
  const [editingTagId, setEditingTagId] = useState<number | null>(null);
  const [editingTagName, setEditingTagName] = useState('');
  const [editingTagCategory, setEditingTagCategory] = useState('');
  const [deletingTagId, setDeletingTagId] = useState<number | null>(null);
  const [showDeleteTagModal, setShowDeleteTagModal] = useState(false);
  const [tagToDelete, setTagToDelete] = useState<Tag | null>(null);
  
  // Tag categories (matching backend TagCategory enum)
  const tagCategories = [
    'Meal Types',
    'Special Dietary',
    'Course Types',
    'Cuisine Types',
    'Main Ingredients',
    'Cooking Methods',
    'Special Categories'
  ];
  
  // Users state
  const [users, setUsers] = useState<User[]>([]);
  const [editingUserId, setEditingUserId] = useState<string | number | null>(null);
  const [editingUserData, setEditingUserData] = useState<{
    email: string;
    full_name: string;
    is_active: boolean;
    is_superuser: boolean;
    password: string;
  }>({ email: '', full_name: '', is_active: true, is_superuser: false, password: '' });
  
  // Recipes state
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [showDeleteRecipeModal, setShowDeleteRecipeModal] = useState(false);
  const [recipeToDelete, setRecipeToDelete] = useState<Recipe | null>(null);
  const [deletingRecipeId, setDeletingRecipeId] = useState<number | null>(null);
  const [userLookup, setUserLookup] = useState<Map<string, User>>(new Map());
  
  // System test state
  const [testResults, setTestResults] = useState<{ [key: string]: any }>({});
  const [testingKey, setTestingKey] = useState<string | null>(null);
  
  // Common state
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Check authorization
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    if (!user?.is_superuser) {
      navigate('/');
      return;
    }
  }, [isAuthenticated, user, navigate]);

  // Load data based on active tab
  useEffect(() => {
    if (user?.is_superuser) {
      if (activeTab === 'tags') {
        loadTags();
      } else if (activeTab === 'users') {
        loadUsers();
      } else if (activeTab === 'recipes') {
        loadRecipes();
      } else {
        setIsLoading(false);
      }
    }
  }, [activeTab, user]);

  // Tag Management Functions
  const loadTags = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const allTags = await apiClient.getAllTags();
      setTags(allTags);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('admin.tags.error'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateTag = async () => {
    if (!newTagName.trim() || !newTagCategory.trim()) return;
    
    setIsCreating(true);
    setError(null);
    try {
      await apiClient.createAdminTag(newTagName.trim(), newTagCategory);
      setNewTagName('');
      setNewTagCategory(''); // Reset to empty
      await loadTags();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('admin.tags.error'));
    } finally {
      setIsCreating(false);
    }
  };

  const handleEditTag = (tag: Tag) => {
    setEditingTagId(tag.id);
    setEditingTagName(tag.name);
    setEditingTagCategory(tag.category);
  };

  const handleSaveTagEdit = async (tagId: number) => {
    if (!editingTagName.trim()) return;
    
    setError(null);
    try {
      await apiClient.updateAdminTag(tagId, editingTagName.trim(), editingTagCategory);
      setEditingTagId(null);
      setEditingTagName('');
      setEditingTagCategory('');
      await loadTags();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('admin.tags.error'));
    }
  };

  const handleCancelTagEdit = () => {
    setEditingTagId(null);
    setEditingTagName('');
    setEditingTagCategory('');
  };

  const handleDeleteTagClick = (tag: Tag) => {
    setTagToDelete(tag);
    setShowDeleteTagModal(true);
  };

  const handleDeleteTagConfirm = async () => {
    if (!tagToDelete) return;
    
    setDeletingTagId(tagToDelete.id);
    setError(null);
    setSuccessMessage(null);
    try {
      const result = await apiClient.deleteAdminTag(tagToDelete.id);
      await loadTags();
      setShowDeleteTagModal(false);
      setTagToDelete(null);
      
      // Show success message with details
      if (result.recipes_affected > 0) {
        setSuccessMessage(
          t('admin.tags.delete_success_with_recipes')
            .replace('{name}', result.tag_name)
            .replace('{count}', String(result.recipes_affected))
        );
      } else {
        setSuccessMessage(
          t('admin.tags.delete_success').replace('{name}', result.tag_name)
        );
      }
      
      // Clear success message after 5 seconds
      setTimeout(() => setSuccessMessage(null), 5000);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('admin.tags.error'));
    } finally {
      setDeletingTagId(null);
    }
  };

  // User Management Functions
  const loadUsers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await apiClient.getAllUsers();
      setUsers(response.users);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('admin.users.error'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditUser = (userToEdit: User) => {
    setEditingUserId(userToEdit.id);
    setEditingUserData({
      email: userToEdit.email,
      full_name: userToEdit.full_name || '',
      is_active: userToEdit.is_active !== undefined ? userToEdit.is_active : true,
      is_superuser: userToEdit.is_superuser || false,
      password: '',
    });
  };

  const handleSaveUserEdit = async () => {
    if (!editingUserId) return;
    
    setError(null);
    try {
      // Update basic user data
      await apiClient.updateUser(editingUserId, {
        email: editingUserData.email,
        full_name: editingUserData.full_name,
        is_active: editingUserData.is_active,
      });
      
      // Update superuser status separately
      await apiClient.setUserSuperuser(editingUserId, editingUserData.is_superuser);
      
      // Update password if provided
      if (editingUserData.password.trim()) {
        await apiClient.updateUserPassword(editingUserId, editingUserData.password);
      }
      
      setEditingUserId(null);
      setEditingUserData({ email: '', full_name: '', is_active: true, is_superuser: false, password: '' });
      await loadUsers();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('admin.users.error'));
    }
  };

  const handleCancelUserEdit = () => {
    setEditingUserId(null);
    setEditingUserData({ email: '', full_name: '', is_active: true, is_superuser: false, password: '' });
  };

  // Recipe Management Functions
  const loadRecipes = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const allRecipes = await apiClient.getAllRecipesForAdmin(1000); // Get ALL recipes (public and private) for admin view
      setRecipes(allRecipes);
      
      // Load users to create a lookup map for recipe authors
      const allUsers = await apiClient.getAllUsers();
      const lookup = new Map<string, User>();
      allUsers.users.forEach(u => {
        if (u.uuid) {
          lookup.set(u.uuid, u);
        }
      });
      setUserLookup(lookup);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('admin.recipes.error'));
    } finally {
      setIsLoading(false);
    }
  };

  const filteredRecipes = recipes.filter(recipe =>
    recipe.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    recipe.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDeleteRecipeClick = (recipe: Recipe) => {
    setRecipeToDelete(recipe);
    setShowDeleteRecipeModal(true);
  };

  const handleDeleteRecipeConfirm = async () => {
    if (!recipeToDelete) return;
    
    setDeletingRecipeId(recipeToDelete.id);
    setError(null);
    try {
      await apiClient.adminDeleteRecipe(recipeToDelete.id);
      await loadRecipes();
      setShowDeleteRecipeModal(false);
      setRecipeToDelete(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('admin.recipes.error'));
    } finally {
      setDeletingRecipeId(null);
    }
  };

  // System Test Functions
  const runSystemTest = async (testName: 'db' | 'config' | 'setup') => {
    setTestingKey(testName);
    setError(null);
    try {
      let result;
      if (testName === 'db') {
        result = await apiClient.testDbConnection();
      } else if (testName === 'config') {
        result = await apiClient.testConfig();
      } else {
        result = await apiClient.testSetup();
      }
      setTestResults({ ...testResults, [testName]: result });
    } catch (err) {
      setTestResults({ 
        ...testResults, 
        [testName]: { 
          status: 'error', 
          message: err instanceof ApiError ? err.message : 'Test failed' 
        } 
      });
    } finally {
      setTestingKey(null);
    }
  };

  // Show unauthorized message for non-superusers
  if (!user?.is_superuser) {
    return (
      <MainLayout>
        <PageContainer
          title={t('admin.title')}
          description={t('admin.unauthorized')}
        >
          <div className="text-center py-8">
            <p className="text-lg text-gray-600 dark:text-gray-300">{t('admin.unauthorized')}</p>
            <Button onClick={() => navigate('/')} className="mt-4">
              {t('nav.home')}
            </Button>
          </div>
        </PageContainer>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <PageContainer
        title={t('admin.title')}
        description={t('admin.description')}
      >
        <div className="space-y-6">
          {/* Tabs */}
          <div className="flex gap-4 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setActiveTab('users')}
              className={`px-4 py-2 font-medium transition-colors border-b-2 ${
                activeTab === 'users'
                  ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              {t('admin.users.title')}
            </button>
            <button
              onClick={() => setActiveTab('recipes')}
              className={`px-4 py-2 font-medium transition-colors border-b-2 ${
                activeTab === 'recipes'
                  ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              {t('admin.recipes.title')}
            </button>
            <button
              onClick={() => setActiveTab('tags')}
              className={`px-4 py-2 font-medium transition-colors border-b-2 ${
                activeTab === 'tags'
                  ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              {t('admin.nav.tags')}
            </button>
            <button
              onClick={() => setActiveTab('system')}
              className={`px-4 py-2 font-medium transition-colors border-b-2 ${
                activeTab === 'system'
                  ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
                  : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
            >
              {t('admin.nav.system')}
            </button>
          </div>

          {/* Error display */}
          {error && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 px-4 py-3 rounded">
              {error}
            </div>
          )}
          
          {/* Success message display */}
          {successMessage && (
            <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-200 px-4 py-3 rounded">
              {successMessage}
            </div>
          )}

          {/* Users Management Tab */}
          {activeTab === 'users' && (
            <Card>
              <CardHeader>
                <CardTitle>{t('admin.users.title')}</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <p className="text-center py-8 text-gray-600 dark:text-gray-300">
                    {t('admin.users.loading')}
                  </p>
                ) : users.length === 0 ? (
                  <p className="text-center py-8 text-gray-600 dark:text-gray-300">
                    {t('admin.users.empty')}
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm text-left">
                      <thead className="text-xs uppercase bg-gray-50 dark:bg-gray-700">
                        <tr>
                          <th className="px-4 py-3">{t('admin.users.email')}</th>
                          <th className="px-4 py-3">{t('admin.users.full_name')}</th>
                          <th className="px-4 py-3">{t('admin.users.uuid')}</th>
                          <th className="px-4 py-3">{t('admin.users.status')}</th>
                          <th className="px-4 py-3">{t('admin.users.role')}</th>
                          <th className="px-4 py-3">{t('admin.users.created_at')}</th>
                          <th className="px-4 py-3">{t('admin.users.updated_at')}</th>
                          <th className="px-4 py-3 text-right">{t('admin.users.actions')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {users.map((u) => (
                          <tr key={u.id} className="border-b dark:border-gray-700">
                            {editingUserId === u.id ? (
                              <>
                                <td className="px-4 py-3">
                                  <Input
                                    value={editingUserData.email}
                                    onChange={(e) => setEditingUserData({ ...editingUserData, email: e.target.value })}
                                    className="max-w-xs"
                                  />
                                </td>
                                <td className="px-4 py-3">
                                  <Input
                                    value={editingUserData.full_name}
                                    onChange={(e) => setEditingUserData({ ...editingUserData, full_name: e.target.value })}
                                    className="max-w-xs"
                                  />
                                </td>
                                <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 font-mono" title={u.uuid || 'N/A'}>
                                  {u.uuid ? `${u.uuid.substring(0, 8)}...` : 'N/A'}
                                </td>
                                <td className="px-4 py-3">
                                  <label className="flex items-center gap-2">
                                    <input
                                      type="checkbox"
                                      checked={editingUserData.is_active}
                                      onChange={(e) => setEditingUserData({ ...editingUserData, is_active: e.target.checked })}
                                    />
                                    <span className="text-xs">{t('admin.users.is_active')}</span>
                                  </label>
                                </td>
                                <td className="px-4 py-3">
                                  <label className="flex items-center gap-2">
                                    <input
                                      type="checkbox"
                                      checked={editingUserData.is_superuser}
                                      onChange={(e) => setEditingUserData({ ...editingUserData, is_superuser: e.target.checked })}
                                    />
                                    <span className="text-xs">{t('admin.users.is_superuser')}</span>
                                  </label>
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                                  {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                                  {u.updated_at ? new Date(u.updated_at).toLocaleDateString() : 'N/A'}
                                </td>
                                <td className="px-4 py-3">
                                  <div className="space-y-2">
                                    <Input
                                      type="password"
                                      placeholder={t('admin.users.password_placeholder')}
                                      value={editingUserData.password}
                                      onChange={(e) => setEditingUserData({ ...editingUserData, password: e.target.value })}
                                      className="max-w-xs"
                                    />
                                    <div className="flex justify-end gap-2">
                                      <Button size="sm" onClick={handleSaveUserEdit}>
                                        {t('admin.users.save')}
                                      </Button>
                                      <Button size="sm" variant="outline" onClick={handleCancelUserEdit}>
                                        {t('admin.users.cancel')}
                                      </Button>
                                    </div>
                                  </div>
                                </td>
                              </>
                            ) : (
                              <>
                                <td className="px-4 py-3">{u.email}</td>
                                <td className="px-4 py-3">{u.full_name || '-'}</td>
                                <td className="px-4 py-3 text-xs text-gray-500 dark:text-gray-400 font-mono" title={u.uuid || 'N/A'}>
                                  {u.uuid ? `${u.uuid.substring(0, 8)}...` : 'N/A'}
                                </td>
                                <td className="px-4 py-3">
                                  <span className={`px-2 py-1 rounded text-xs ${
                                    u.is_active 
                                      ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                                  }`}>
                                    {u.is_active ? t('admin.users.active') : t('admin.users.inactive')}
                                  </span>
                                </td>
                                <td className="px-4 py-3">
                                  <span className={`px-2 py-1 rounded text-xs ${
                                    u.is_superuser 
                                      ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200' 
                                      : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                                  }`}>
                                    {u.is_superuser ? t('admin.users.superuser') : t('admin.users.regular')}
                                  </span>
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                                  {u.created_at ? new Date(u.created_at).toLocaleDateString() : 'N/A'}
                                </td>
                                <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                                  {u.updated_at ? new Date(u.updated_at).toLocaleDateString() : 'N/A'}
                                </td>
                                <td className="px-4 py-3 text-right">
                                  <div className="flex justify-end gap-2">
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={() => handleEditUser(u)}
                                    >
                                      {t('admin.users.edit')}
                                    </Button>
                                  </div>
                                </td>
                              </>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Recipes Management Tab */}
          {activeTab === 'recipes' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>{t('admin.recipes.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="mb-4">
                    <Input
                      type="search"
                      placeholder={t('admin.recipes.search_placeholder')}
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  {isLoading ? (
                    <p className="text-center py-8 text-gray-600 dark:text-gray-300">
                      {t('admin.recipes.loading')}
                    </p>
                  ) : filteredRecipes.length === 0 ? (
                    <p className="text-center py-8 text-gray-600 dark:text-gray-300">
                      {t('admin.recipes.empty')}
                    </p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm text-left">
                        <thead className="text-xs uppercase bg-gray-50 dark:bg-gray-700">
                          <tr>
                            <th className="px-4 py-3">{t('admin.recipes.recipe_title')}</th>
                            <th className="px-4 py-3">{t('admin.recipes.author')}</th>
                            <th className="px-4 py-3">{t('admin.recipes.status')}</th>
                            <th className="px-4 py-3">{t('admin.recipes.created')}</th>
                            <th className="px-4 py-3 text-right">{t('admin.recipes.actions')}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {filteredRecipes.map((recipe) => (
                            <tr key={recipe.id} className="border-b dark:border-gray-700">
                              <td className="px-4 py-3 font-medium">{recipe.title}</td>
                              <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                                {(() => {
                                  const author = userLookup.get(recipe.user_id);
                                  return author ? (author.full_name || author.email) : recipe.user_id;
                                })()}
                              </td>
                              <td className="px-4 py-3">
                                <span className={`px-2 py-1 rounded text-xs ${
                                  recipe.is_public 
                                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' 
                                    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                                }`}>
                                  {recipe.is_public ? t('admin.recipes.public') : t('admin.recipes.private')}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                                {new Date(recipe.created_at).toLocaleDateString()}
                              </td>
                              <td className="px-4 py-3 text-right">
                                <div className="flex justify-end gap-2">
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => navigate(`/recipes/${recipe.id}`)}
                                  >
                                    {t('admin.recipes.view')}
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => navigate(`/recipes/${recipe.id}/edit`)}
                                  >
                                    {t('admin.recipes.edit')}
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="destructive"
                                    onClick={() => handleDeleteRecipeClick(recipe)}
                                    disabled={deletingRecipeId === recipe.id}
                                  >
                                    {t('admin.recipes.delete')}
                                  </Button>
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* Tags Management Tab */}
          {activeTab === 'tags' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>{t('admin.tags.create')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex gap-4">
                      <div className="flex-1">
                        <label className="block text-sm font-medium mb-2">{t('admin.tags.name')}</label>
                        <Input
                          value={newTagName}
                          onChange={(e) => setNewTagName(e.target.value)}
                          placeholder={t('admin.tags.name_placeholder')}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' && newTagName.trim()) {
                              handleCreateTag();
                            }
                          }}
                          disabled={isCreating}
                        />
                      </div>
                      <div className="flex-1">
                        <label className="block text-sm font-medium mb-2">{t('admin.tags.category')}</label>
                        <select
                          value={newTagCategory}
                          onChange={(e) => setNewTagCategory(e.target.value)}
                          disabled={isCreating}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
                        >
                          <option value="">{t('admin.tags.category_placeholder')}</option>
                          {tagCategories.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                          ))}
                        </select>
                      </div>
                      <div className="flex items-end">
                        <Button 
                          onClick={handleCreateTag} 
                          disabled={!newTagName.trim() || !newTagCategory.trim() || isCreating}
                        >
                          {isCreating ? t('admin.tags.creating') : t('admin.tags.create')}
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('admin.tags.title')}</CardTitle>
                </CardHeader>
                <CardContent>
                  {isLoading ? (
                    <p className="text-center py-8 text-gray-600 dark:text-gray-300">
                      {t('admin.tags.loading')}
                    </p>
                  ) : tags.length === 0 ? (
                    <p className="text-center py-8 text-gray-600 dark:text-gray-300">
                      {t('admin.tags.empty')}
                    </p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm text-left">
                        <thead className="text-xs uppercase bg-gray-50 dark:bg-gray-700">
                          <tr>
                            <th className="px-4 py-3">{t('admin.tags.name')}</th>
                            <th className="px-4 py-3">{t('admin.tags.category')}</th>
                            <th className="px-4 py-3 text-right">{t('admin.tags.recipe_count')}</th>
                            <th className="px-4 py-3 text-right">{t('admin.tags.actions')}</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tags.map((tag) => (
                            <tr key={tag.id} className="border-b dark:border-gray-700">
                              <td className="px-4 py-3">
                                {editingTagId === tag.id ? (
                                  <Input
                                    value={editingTagName}
                                    onChange={(e) => setEditingTagName(e.target.value)}
                                    onKeyDown={(e) => {
                                      if (e.key === 'Enter') {
                                        handleSaveTagEdit(tag.id);
                                      } else if (e.key === 'Escape') {
                                        handleCancelTagEdit();
                                      }
                                    }}
                                    className="max-w-xs"
                                  />
                                ) : (
                                  tag.name
                                )}
                              </td>
                              <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                                {editingTagId === tag.id ? (
                                  <select
                                    value={editingTagCategory}
                                    onChange={(e) => setEditingTagCategory(e.target.value)}
                                    className="w-full px-2 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
                                  >
                                    {tagCategories.map(cat => (
                                      <option key={cat} value={cat}>{cat}</option>
                                    ))}
                                  </select>
                                ) : (
                                  tag.category
                                )}
                              </td>
                              <td className="px-4 py-3 text-right text-gray-600 dark:text-gray-400">
                                {tag.recipe_counter}
                              </td>
                              <td className="px-4 py-3 text-right">
                                <div className="flex justify-end gap-2">
                                  {editingTagId === tag.id ? (
                                    <>
                                      <Button
                                        size="sm"
                                        onClick={() => handleSaveTagEdit(tag.id)}
                                        disabled={!editingTagName.trim()}
                                      >
                                        {t('admin.tags.save')}
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={handleCancelTagEdit}
                                      >
                                        {t('admin.tags.cancel')}
                                      </Button>
                                    </>
                                  ) : (
                                    <>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => handleEditTag(tag)}
                                      >
                                        {t('admin.tags.edit')}
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="destructive"
                                        onClick={() => handleDeleteTagClick(tag)}
                                        disabled={deletingTagId === tag.id}
                                      >
                                        {deletingTagId === tag.id 
                                          ? t('admin.tags.deleting') 
                                          : t('admin.tags.delete')
                                        }
                                      </Button>
                                    </>
                                  )}
                                </div>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          )}

          {/* System Tests Tab */}
          {activeTab === 'system' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>{t('admin.system.title')}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Database Connection Test */}
                  <div className="flex items-center justify-between p-4 border rounded dark:border-gray-700">
                    <div>
                      <h3 className="font-medium">{t('admin.system.db_connection')}</h3>
                      {testResults.db && (
                        <p className={`text-sm mt-1 ${
                          testResults.db.status === 'success' 
                            ? 'text-green-600 dark:text-green-400' 
                            : 'text-red-600 dark:text-red-400'
                        }`}>
                          {testResults.db.message}
                        </p>
                      )}
                    </div>
                    <Button
                      onClick={() => runSystemTest('db')}
                      disabled={testingKey === 'db'}
                    >
                      {testingKey === 'db' ? t('admin.system.testing') : t('admin.system.test')}
                    </Button>
                  </div>

                  {/* Config Test */}
                  <div className="flex items-center justify-between p-4 border rounded dark:border-gray-700">
                    <div className="flex-1">
                      <h3 className="font-medium">{t('admin.system.config')}</h3>
                      {testResults.config && (
                        <pre className="text-xs mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded overflow-auto max-h-40">
                          {JSON.stringify(testResults.config, null, 2)}
                        </pre>
                      )}
                    </div>
                    <Button
                      onClick={() => runSystemTest('config')}
                      disabled={testingKey === 'config'}
                      className="ml-4"
                    >
                      {testingKey === 'config' ? t('admin.system.testing') : t('admin.system.test')}
                    </Button>
                  </div>

                  {/* Setup Test */}
                  <div className="flex items-center justify-between p-4 border rounded dark:border-gray-700">
                    <div className="flex-1">
                      <h3 className="font-medium">{t('admin.system.setup')}</h3>
                      {testResults.setup && (
                        <pre className="text-xs mt-2 p-2 bg-gray-100 dark:bg-gray-800 rounded overflow-auto max-h-40">
                          {JSON.stringify(testResults.setup, null, 2)}
                        </pre>
                      )}
                    </div>
                    <Button
                      onClick={() => runSystemTest('setup')}
                      disabled={testingKey === 'setup'}
                      className="ml-4"
                    >
                      {testingKey === 'setup' ? t('admin.system.testing') : t('admin.system.test')}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Delete Tag Confirmation Modal */}
        <ConfirmationModal
          isOpen={showDeleteTagModal}
          onClose={() => setShowDeleteTagModal(false)}
          onConfirm={handleDeleteTagConfirm}
          title={t('admin.tags.delete_confirm_title')}
          message={t('admin.tags.delete_confirm_message').replace('{name}', tagToDelete?.name || '')}
          confirmText={t('admin.tags.delete')}
          cancelText={t('modal.cancel')}
          variant="destructive"
          isLoading={deletingTagId !== null}
        />

        {/* Delete Recipe Confirmation Modal */}
        <ConfirmationModal
          isOpen={showDeleteRecipeModal}
          onClose={() => setShowDeleteRecipeModal(false)}
          onConfirm={handleDeleteRecipeConfirm}
          title={t('admin.recipes.delete_confirm_title')}
          message={t('admin.recipes.delete_confirm_message').replace('{title}', recipeToDelete?.title || '')}
          confirmText={t('admin.recipes.delete')}
          cancelText={t('modal.cancel')}
          variant="destructive"
          isLoading={deletingRecipeId !== null}
        />
      </PageContainer>
    </MainLayout>
  );
};

export default AdminPage;
