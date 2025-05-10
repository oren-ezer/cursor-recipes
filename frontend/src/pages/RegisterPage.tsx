import React from 'react';
import { Link } from 'react-router-dom';

const RegisterPage: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 dark:bg-gray-900 p-4 text-center">
      <div className="bg-white dark:bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full">
        <h1 className="text-4xl font-bold text-indigo-600 dark:text-indigo-400 mb-6">Coming Soon!</h1>
        <p className="text-lg text-gray-700 dark:text-gray-300 mb-8">
          Our registration page is currently under construction. We're working hard to bring it to you!
        </p>
        <img src="/undraw_under_construction_light.svg" alt="Under Construction" className="mx-auto mb-8 w-64 h-auto block dark:hidden" />
        <img src="/undraw_under_construction_dark.svg" alt="Under Construction" className="mx-auto mb-8 w-64 h-auto hidden dark:block" />
        <Link 
          to="/"
          className="mt-4 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-md transition duration-150 ease-in-out"
        >
          Go Back to Home
        </Link>
      </div>
      <p className="mt-8 text-sm text-gray-500 dark:text-gray-400">
        In the meantime, you can explore other parts of our site.
      </p>
    </div>
  );
};

export default RegisterPage; 