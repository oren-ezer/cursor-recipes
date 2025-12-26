import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../contexts/LanguageContext';
import { apiClient, ApiError } from '../lib/api-client';
import type { Tag } from '../lib/api-client';
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

  const [activeTab, setActiveTab] = useState<'tags' | 'system'>('tags');
  const [tags, setTags] = useState<Tag[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Tag management state
  const [isCreating, setIsCreating] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [editingTagId, setEditingTagId] = useState<number | null>(null);
  const [editingTagName, setEditingTagName] = useState('');
  const [deletingTagId, setDeletingTagId] = useState<number | null>(null);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [tagToDelete, setTagToDelete] = useState<Tag | null>(null);
  
  // System test state
  const [testResults, setTestResults] = useState<{ [key: string]: any }>({});
  const [testingKey, setTestingKey] = useState<string | null>(null);

  // Check authorization
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    
    if (!user?.is_superuser) {
      // Redirect non-superusers
      navigate('/');
      return;
    }
  }, [isAuthenticated, user, navigate]);

  // Load tags
  useEffect(() => {
    if (activeTab === 'tags' && user?.is_superuser) {
      loadTags();
    }
  }, [activeTab, user]);

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
    if (!newTagName.trim()) return;
    
    setIsCreating(true);
    setError(null);
    try {
      await apiClient.createAdminTag(newTagName.trim());
      setNewTagName('');
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
  };

  const handleSaveEdit = async (tagId: number) => {
    if (!editingTagName.trim()) return;
    
    setError(null);
    try {
      await apiClient.updateAdminTag(tagId, editingTagName.trim());
      setEditingTagId(null);
      setEditingTagName('');
      await loadTags();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('admin.tags.error'));
    }
  };

  const handleCancelEdit = () => {
    setEditingTagId(null);
    setEditingTagName('');
  };

  const handleDeleteClick = (tag: Tag) => {
    setTagToDelete(tag);
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (!tagToDelete) return;
    
    setDeletingTagId(tagToDelete.id);
    setError(null);
    try {
      await apiClient.deleteAdminTag(tagToDelete.id);
      await loadTags();
      setShowDeleteModal(false);
      setTagToDelete(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : t('admin.tags.error'));
    } finally {
      setDeletingTagId(null);
    }
  };

  const handleDeleteCancel = () => {
    setShowDeleteModal(false);
    setTagToDelete(null);
  };

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

          {/* Tags Management Tab */}
          {activeTab === 'tags' && (
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>{t('admin.tags.create')}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex gap-4">
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
                    <Button 
                      onClick={handleCreateTag} 
                      disabled={!newTagName.trim() || isCreating}
                    >
                      {isCreating ? t('admin.tags.creating') : t('admin.tags.create')}
                    </Button>
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
                                        handleSaveEdit(tag.id);
                                      } else if (e.key === 'Escape') {
                                        handleCancelEdit();
                                      }
                                    }}
                                    className="max-w-xs"
                                  />
                                ) : (
                                  tag.name
                                )}
                              </td>
                              <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                                {tag.category}
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
                                        onClick={() => handleSaveEdit(tag.id)}
                                        disabled={!editingTagName.trim()}
                                      >
                                        {t('admin.tags.save')}
                                      </Button>
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={handleCancelEdit}
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
                                        onClick={() => handleDeleteClick(tag)}
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
                    <div>
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
                    >
                      {testingKey === 'config' ? t('admin.system.testing') : t('admin.system.test')}
                    </Button>
                  </div>

                  {/* Setup Test */}
                  <div className="flex items-center justify-between p-4 border rounded dark:border-gray-700">
                    <div>
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
                    >
                      {testingKey === 'setup' ? t('admin.system.testing') : t('admin.system.test')}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </div>

        {/* Delete Confirmation Modal */}
        <ConfirmationModal
          isOpen={showDeleteModal}
          onClose={handleDeleteCancel}
          onConfirm={handleDeleteConfirm}
          title={t('admin.tags.delete_confirm_title')}
          message={t('admin.tags.delete_confirm_message').replace('{name}', tagToDelete?.name || '')}
          confirmText={t('admin.tags.delete')}
          cancelText={t('modal.cancel')}
          variant="destructive"
          isLoading={deletingTagId !== null}
        />
      </PageContainer>
    </MainLayout>
  );
};

export default AdminPage;

