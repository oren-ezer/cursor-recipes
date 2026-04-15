import React, { useState, useRef, useCallback } from 'react';
import { Upload, X, ImageIcon, Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';
import { apiClient, type ImageInfo } from '../lib/api-client';
import { useLanguage } from '../contexts/LanguageContext';
import { Button } from './ui/button';

const MAX_FILE_SIZE_MB = 10;
const MAX_FILES = 5;
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp'];

export interface ImageUploaderProps {
  onUploadComplete?: (images: ImageInfo[]) => void;
  recipeId?: number;
  maxFiles?: number;
  maxSizeMb?: number;
  className?: string;
  disabled?: boolean;
}

interface PreviewFile {
  file: File;
  previewUrl: string;
}

const ImageUploader: React.FC<ImageUploaderProps> = ({
  onUploadComplete,
  recipeId,
  maxFiles = MAX_FILES,
  maxSizeMb = MAX_FILE_SIZE_MB,
  className,
  disabled = false,
}) => {
  const { t } = useLanguage();
  const [previews, setPreviews] = useState<PreviewFile[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadedImages, setUploadedImages] = useState<ImageInfo[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateFile = useCallback(
    (file: File): string | null => {
      if (!ACCEPTED_TYPES.includes(file.type)) {
        return t('image_upload.invalid_type');
      }
      if (file.size > maxSizeMb * 1024 * 1024) {
        return `${file.name} ${t('image_upload.max_size')}`;
      }
      return null;
    },
    [maxSizeMb, t]
  );

  const addFiles = useCallback(
    (files: FileList | File[]) => {
      setError(null);
      const fileArray = Array.from(files);

      if (previews.length + fileArray.length > maxFiles) {
        setError(`${t('image_upload.max_files')} (${maxFiles})`);
        return;
      }

      for (const file of fileArray) {
        const err = validateFile(file);
        if (err) {
          setError(err);
          return;
        }
      }

      const newPreviews: PreviewFile[] = fileArray.map((file) => ({
        file,
        previewUrl: URL.createObjectURL(file),
      }));

      setPreviews((prev) => [...prev, ...newPreviews]);
    },
    [previews.length, maxFiles, validateFile, t]
  );

  const removeFile = useCallback((index: number) => {
    setPreviews((prev) => {
      const removed = prev[index];
      if (removed) URL.revokeObjectURL(removed.previewUrl);
      return prev.filter((_, i) => i !== index);
    });
    setError(null);
  }, []);

  const handleUpload = useCallback(async () => {
    if (previews.length === 0) return;
    setUploading(true);
    setError(null);

    try {
      const files = previews.map((p) => p.file);
      const response = await apiClient.uploadImages(files, recipeId);
      setUploadedImages(response.images);
      onUploadComplete?.(response.images);
      previews.forEach((p) => URL.revokeObjectURL(p.previewUrl));
      setPreviews([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : t('image_upload.error'));
    } finally {
      setUploading(false);
    }
  }, [previews, recipeId, onUploadComplete, t]);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);
      if (e.dataTransfer.files?.length) {
        addFiles(e.dataTransfer.files);
      }
    },
    [addFiles]
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      if (e.target.files?.length) {
        addFiles(e.target.files);
      }
      if (inputRef.current) inputRef.current.value = '';
    },
    [addFiles]
  );

  return (
    <div className={cn('space-y-4', className)}>
      {/* Drop zone */}
      <div
        onDragEnter={handleDrag}
        onDragOver={handleDrag}
        onDragLeave={handleDrag}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={cn(
          'flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 text-center transition-colors cursor-pointer',
          dragActive
            ? 'border-primary bg-primary/5'
            : 'border-muted-foreground/25 hover:border-primary/50',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
        role="button"
        tabIndex={0}
        aria-label={t('image_upload.drag_drop')}
      >
        <Upload className="h-10 w-10 text-muted-foreground mb-3" />
        <p className="text-sm font-medium">{t('image_upload.drag_drop')}</p>
        <p className="text-xs text-muted-foreground mt-1">
          {t('image_upload.browse')}
        </p>
        <input
          ref={inputRef}
          type="file"
          multiple
          accept={ACCEPTED_TYPES.join(',')}
          onChange={handleInputChange}
          className="hidden"
          disabled={disabled}
          data-testid="file-input"
        />
      </div>

      {/* Previews */}
      {previews.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          {previews.map((p, i) => (
            <div key={i} className="relative group rounded-lg overflow-hidden border">
              <img
                src={p.previewUrl}
                alt={p.file.name}
                className="w-full h-32 object-cover"
              />
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeFile(i);
                }}
                className="absolute top-1 right-1 rtl:right-auto rtl:left-1 rounded-full bg-destructive/80 text-destructive-foreground p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                aria-label={t('image_upload.remove')}
              >
                <X className="h-3 w-3" />
              </button>
              <p className="text-xs truncate px-2 py-1">{p.file.name}</p>
            </div>
          ))}
        </div>
      )}

      {/* Upload button */}
      {previews.length > 0 && (
        <Button
          onClick={handleUpload}
          disabled={uploading || disabled}
          className="w-full"
        >
          {uploading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              {t('image_upload.uploading')}
            </>
          ) : (
            <>
              <Upload className="h-4 w-4" />
              {t('image_upload.title')} ({previews.length})
            </>
          )}
        </Button>
      )}

      {/* Uploaded images */}
      {uploadedImages.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-green-600">
            {t('image_upload.success')}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {uploadedImages.map((img) => (
              <div key={img.image_id} className="rounded-lg overflow-hidden border">
                <img
                  src={img.serving_url}
                  alt={img.filename}
                  className="w-full h-32 object-cover"
                />
                <div className="flex items-center gap-1 px-2 py-1">
                  <ImageIcon className="h-3 w-3 text-muted-foreground" />
                  <p className="text-xs truncate">{img.filename}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error */}
      {error && (
        <p className="text-sm text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
};

export default ImageUploader;
