import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorId: string | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
    errorId: null
  };

  private isDevelopment = import.meta.env.DEV;

  public static getDerivedStateFromError(error: Error): Partial<State> {
    // Generate a unique error ID for tracking
    const errorId = `ERR-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    return { hasError: true, error, errorInfo: null, errorId };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Always log to console (will be sent to server logs in production)
    console.error('ErrorBoundary caught an error:', {
      errorId: this.state.errorId,
      error: error,
      errorInfo: errorInfo,
      timestamp: new Date().toISOString()
    });

    // In production, you could send this to an error tracking service (Sentry, LogRocket, etc.)
    if (!this.isDevelopment) {
      // Example: sendToErrorTracking(error, errorInfo, this.state.errorId);
    }

    this.setState({ error, errorInfo });
  }

  private handleReload = () => {
    window.location.reload();
  };

  private handleGoHome = () => {
    window.location.href = '/';
  };

  private renderDevelopmentError() {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="max-w-3xl w-full bg-white dark:bg-gray-800 rounded-lg shadow-xl p-6">
          {/* Header */}
          <div className="flex items-center gap-3 mb-4">
            <svg className="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                Development Error
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Error ID: {this.state.errorId}
              </p>
            </div>
          </div>

          {/* Error Message */}
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
            <h2 className="text-lg font-semibold text-red-900 dark:text-red-200 mb-2">
              {this.state.error?.name || 'Error'}
            </h2>
            <p className="text-red-800 dark:text-red-300 font-mono text-sm">
              {this.state.error?.message}
            </p>
          </div>

          {/* Stack Trace */}
          {this.state.error?.stack && (
            <details className="mb-4">
              <summary className="cursor-pointer font-semibold text-gray-700 dark:text-gray-300 mb-2 hover:text-indigo-600 dark:hover:text-indigo-400">
                Stack Trace
              </summary>
              <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-4 rounded-md overflow-x-auto border border-gray-200 dark:border-gray-700">
                <code className="text-gray-800 dark:text-gray-200">{this.state.error.stack}</code>
              </pre>
            </details>
          )}

          {/* Component Stack */}
          {this.state.errorInfo?.componentStack && (
            <details className="mb-4">
              <summary className="cursor-pointer font-semibold text-gray-700 dark:text-gray-300 mb-2 hover:text-indigo-600 dark:hover:text-indigo-400">
                Component Stack
              </summary>
              <pre className="text-xs bg-gray-100 dark:bg-gray-900 p-4 rounded-md overflow-x-auto border border-gray-200 dark:border-gray-700">
                <code className="text-gray-800 dark:text-gray-200">{this.state.errorInfo.componentStack}</code>
              </pre>
            </details>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={this.handleReload}
              className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md font-medium transition-colors"
            >
              Reload Page
            </button>
            <button
              onClick={this.handleGoHome}
              className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 rounded-md font-medium transition-colors"
            >
              Go to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  private renderProductionError() {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-lg shadow-xl p-8 text-center">
          {/* Error Icon */}
          <div className="mb-6 flex justify-center">
            <div className="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-red-600 dark:text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
          </div>

          {/* Error Message */}
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-3">
            Oops! Something went wrong
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            We're sorry for the inconvenience. An unexpected error occurred. 
            Please try reloading the page or return to the home page.
          </p>

          {/* Reference ID (safe to show) */}
          <p className="text-sm text-gray-500 dark:text-gray-500 mb-6 font-mono">
            Reference ID: {this.state.errorId}
          </p>

          {/* Actions */}
          <div className="space-y-3">
            <button
              onClick={this.handleReload}
              className="w-full px-4 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md font-medium transition-colors"
            >
              Reload Page
            </button>
            <button
              onClick={this.handleGoHome}
              className="w-full px-4 py-3 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 rounded-md font-medium transition-colors"
            >
              Go to Home
            </button>
          </div>
        </div>
      </div>
    );
  }

  public render() {
    if (this.state.hasError) {
      return this.isDevelopment ? this.renderDevelopmentError() : this.renderProductionError();
    }

    return this.props.children;
  }
}

export default ErrorBoundary;

