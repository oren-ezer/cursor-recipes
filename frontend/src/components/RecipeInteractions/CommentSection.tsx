import React, { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { apiClient } from '../../lib/api-client';
import type { RecipeComment } from '../../lib/api-client';
import { useLanguage } from '../../contexts/LanguageContext';
import { useAuth } from '../../contexts/AuthContext';
import { CommentItem } from './CommentItem';
import { MessageSquare } from 'lucide-react';

interface CommentSectionProps {
  recipeId: number;
}

export const CommentSection: React.FC<CommentSectionProps> = ({ recipeId }) => {
  const [comments, setComments] = useState<RecipeComment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { t } = useLanguage();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    loadComments();
  }, [recipeId]);

  const loadComments = async () => {
    try {
      const data = await apiClient.getComments(recipeId);
      setComments(data);
    } catch (err) {
      console.error('Failed to load comments:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !isAuthenticated) return;

    setIsSubmitting(true);
    try {
      const created = await apiClient.addComment(recipeId, newComment);
      setComments([created, ...comments]);
      setNewComment('');
    } catch (err) {
      console.error('Failed to post comment:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdate = (updated: RecipeComment) => {
    setComments(comments.map(c => c.id === updated.id ? updated : c));
  };

  const handleDelete = (id: number) => {
    setComments(comments.filter(c => c.id !== id));
  };

  return (
    <div className="mt-8 border-t border-gray-200 dark:border-gray-800 pt-8">
      <div className="flex items-center gap-2 mb-6">
        <MessageSquare className="w-5 h-5 text-gray-500" />
        <h3 className="text-xl font-semibold">{t('interactions.comments.title')}</h3>
        <span className="text-sm text-gray-500 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded-full">
          {comments.length}
        </span>
      </div>

      {isAuthenticated ? (
        <form onSubmit={handleSubmit} className="mb-8">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder={t('interactions.comments.add')}
            className="w-full p-3 border border-gray-200 rounded-lg dark:bg-gray-900 dark:border-gray-700 min-h-[100px] focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y mb-2 text-sm"
            disabled={isSubmitting}
          />
          <div className="flex justify-end">
            <Button type="submit" disabled={isSubmitting || !newComment.trim()}>
              {t('interactions.comments.post')}
            </Button>
          </div>
        </form>
      ) : (
        <div className="bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4 mb-8 text-center text-sm text-gray-600 dark:text-gray-400">
          Please login to join the conversation.
        </div>
      )}

      <div className="space-y-2">
        {isLoading ? (
          <div className="text-center py-8 text-gray-500">Loading comments...</div>
        ) : comments.length > 0 ? (
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden">
            {comments.map((comment) => (
              <CommentItem 
                key={comment.id}
                comment={comment}
                onUpdate={handleUpdate}
                onDelete={handleDelete}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800/30 rounded-xl border border-dashed border-gray-200 dark:border-gray-800">
            {t('interactions.comments.empty')}
          </div>
        )}
      </div>
    </div>
  );
};