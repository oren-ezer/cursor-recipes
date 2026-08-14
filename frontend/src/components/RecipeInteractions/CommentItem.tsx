import React, { useState } from 'react';
import { Edit2, Trash2, SmilePlus } from 'lucide-react';
import { Button } from '../ui/button';
import { apiClient } from '../../lib/api-client';
import type { RecipeComment } from '../../lib/api-client';
import { useLanguage } from '../../contexts/LanguageContext';
import { useAuth } from '../../contexts/AuthContext';

interface CommentItemProps {
  comment: RecipeComment;
  onUpdate: (updated: RecipeComment) => void;
  onDelete: (id: number) => void;
}

export const CommentItem: React.FC<CommentItemProps> = ({ comment, onUpdate, onDelete }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(comment.content);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showActions, setShowActions] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const { t } = useLanguage();
  const { user, isAuthenticated } = useAuth();

  const isOwner = user?.uuid === comment.user_id;
  const canEditDelete = isOwner || user?.is_superuser;

  const handleSaveEdit = async () => {
    if (!editContent.trim() || editContent === comment.content) {
      setIsEditing(false);
      return;
    }

    setIsSubmitting(true);
    try {
      const updated = await apiClient.updateComment(comment.id, editContent);
      onUpdate(updated);
      setIsEditing(false);
    } catch (err) {
      console.error('Failed to update comment:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm(t('interactions.comments.delete_confirm'))) return;
    
    setIsSubmitting(true);
    try {
      await apiClient.deleteComment(comment.id);
      onDelete(comment.id);
    } catch (err) {
      console.error('Failed to delete comment:', err);
      setIsSubmitting(false);
    }
  };

  const toggleReaction = async (reactionType: string) => {
    if (!isAuthenticated) return;
    
    try {
      const response = await apiClient.toggleCommentReaction(comment.id, reactionType);
      
      // Optimistically update reactions
      const currentReactions = comment.reactions || { counts: {} };
      const newCounts = { ...currentReactions.counts };
      
      // Remove old reaction if existed
      if (currentReactions.user_reaction) {
        newCounts[currentReactions.user_reaction] = Math.max(0, (newCounts[currentReactions.user_reaction] || 1) - 1);
      }
      
      let newUserReaction: string | undefined = undefined;
      
      // Add new reaction if not just removed
      if (response.status !== 'removed') {
        newCounts[reactionType] = (newCounts[reactionType] || 0) + 1;
        newUserReaction = reactionType;
      }
      
      onUpdate({
        ...comment,
        reactions: {
          counts: newCounts,
          user_reaction: newUserReaction
        }
      });
    } catch (err) {
      console.error('Failed to toggle reaction:', err);
    }
  };

  const reactions = [
    { type: 'like', icon: '👍', label: t('interactions.reactions.like') },
    { type: 'love', icon: '❤️', label: t('interactions.reactions.love') },
    { type: 'funny', icon: '😂', label: t('interactions.reactions.funny') },
    { type: 'delicious', icon: '🤤', label: t('interactions.reactions.delicious') }
  ];

  return (
    <div 
      className="p-4 border-b border-gray-100 dark:border-gray-800 last:border-0 hover:bg-gray-50/50 dark:hover:bg-gray-800/50 transition-colors"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="flex justify-between items-start gap-4">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-medium text-sm">{comment.user_full_name || 'User'}</span>
            <span className="text-xs text-gray-500">
              {new Date(comment.created_at).toLocaleDateString()}
            </span>
          </div>
          
          {isEditing ? (
            <div className="mt-2 space-y-2">
              <textarea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                className="w-full p-2 border rounded-md dark:bg-gray-800 dark:border-gray-700 min-h-[80px]"
                disabled={isSubmitting}
              />
              <div className="flex gap-2">
                <Button size="sm" onClick={handleSaveEdit} disabled={isSubmitting || !editContent.trim()}>
                  {t('interactions.comments.save')}
                </Button>
                <Button size="sm" variant="outline" onClick={() => setIsEditing(false)} disabled={isSubmitting}>
                  {t('interactions.comments.cancel')}
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-line text-sm">
              {comment.content}
            </p>
          )}
          
          {!isEditing && (
            <div className="flex items-center gap-2 mt-3 relative">
              {isAuthenticated && (
                <button
                  onClick={() => setShowEmojiPicker(!showEmojiPicker)}
                  className="flex items-center justify-center h-6 w-6 rounded-full bg-gray-100 text-gray-500 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700 transition-colors"
                  title="Add reaction"
                >
                  <SmilePlus className="w-4 h-4" />
                </button>
              )}
              
              {reactions.map(({ type, icon, label }) => {
                const count = comment.reactions?.counts[type] || 0;
                const isUserReaction = comment.reactions?.user_reaction === type;
                
                if (count === 0 && !showEmojiPicker && !isUserReaction) return null;
                
                return (
                  <button
                    key={type}
                    onClick={() => {
                      toggleReaction(type);
                      setShowEmojiPicker(false);
                    }}
                    disabled={!isAuthenticated}
                    title={label}
                    className={`flex items-center gap-1 text-xs px-2 py-1 rounded-full transition-colors ${
                      isUserReaction 
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300' 
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'
                    }`}
                  >
                    <span>{icon}</span>
                    {count > 0 && <span>{count}</span>}
                  </button>
                );
              })}
            </div>
          )}
        </div>
        
        {canEditDelete && !isEditing && (
          <div className={`flex items-center ${showActions ? 'opacity-100' : 'opacity-0'} transition-opacity`}>
            <Button variant="ghost" size="sm" onClick={() => setIsEditing(true)} className="h-8 w-8 p-0" title={t('interactions.comments.edit')}>
              <Edit2 className="w-4 h-4 text-gray-500" />
            </Button>
            <Button variant="ghost" size="sm" onClick={handleDelete} className="h-8 w-8 p-0" title={t('interactions.comments.delete')}>
              <Trash2 className="w-4 h-4 text-red-500" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};