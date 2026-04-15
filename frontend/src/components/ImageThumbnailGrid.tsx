import React, { useState } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import type { ImageInfo } from '../lib/api-client';
import ImageLightbox from './ImageLightbox';

interface ImageThumbnailGridProps {
  images: ImageInfo[];
  /** When provided, a delete button appears on each thumbnail */
  onDelete?: (imageId: string) => void;
  deletingId?: string | null;
}

const ImageThumbnailGrid: React.FC<ImageThumbnailGridProps> = ({
  images,
  onDelete,
  deletingId,
}) => {
  const { t } = useLanguage();
  const [lightboxIndex, setLightboxIndex] = useState<number | null>(null);

  if (images.length === 0) return null;

  return (
    <>
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2">
        {images.map((img, idx) => (
          <div key={img.image_id} className="group relative aspect-square">
            <button
              type="button"
              onClick={() => setLightboxIndex(idx)}
              className="h-full w-full overflow-hidden rounded-lg border border-border focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <img
                src={img.serving_url}
                alt={img.filename}
                className="h-full w-full object-cover transition-transform group-hover:scale-105"
              />
            </button>

            {onDelete && (
              <button
                type="button"
                onClick={() => onDelete(img.image_id)}
                disabled={deletingId === img.image_id}
                className="absolute top-1 right-1 rounded-full bg-red-600/80 p-1 text-white opacity-0 transition-opacity group-hover:opacity-100 hover:bg-red-700 disabled:opacity-50"
                aria-label={t('image_upload.delete')}
              >
                {deletingId === img.image_id ? (
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
                    <circle cx="12" cy="12" r="10" className="opacity-25" />
                    <path d="M4 12a8 8 0 018-8" className="opacity-75" />
                  </svg>
                ) : (
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                )}
              </button>
            )}
          </div>
        ))}
      </div>

      {lightboxIndex !== null && (
        <ImageLightbox
          images={images}
          currentIndex={lightboxIndex}
          onClose={() => setLightboxIndex(null)}
          onNavigate={setLightboxIndex}
        />
      )}
    </>
  );
};

export default ImageThumbnailGrid;
