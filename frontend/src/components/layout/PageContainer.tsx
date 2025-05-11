import React from 'react';

interface PageContainerProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  className?: string;
}

const PageContainer: React.FC<PageContainerProps> = ({
  children,
  title,
  description,
  className = '',
}) => {
  return (
    <div className={`px-4 py-6 sm:px-0 bg-white dark:bg-gray-800 shadow rounded-lg ${className}`}>
      {(title || description) && (
        <div className="mb-6 px-4 sm:px-6">
          {title && (
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              {title}
            </h1>
          )}
          {description && (
            <p className="mt-2 text-lg text-gray-600 dark:text-gray-300">
              {description}
            </p>
          )}
        </div>
      )}
      <div className="px-4 sm:px-6">
        {children}
      </div>
    </div>
  );
};

export default PageContainer; 