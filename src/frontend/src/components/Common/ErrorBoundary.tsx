import { Component, type ErrorInfo, type ReactNode } from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

// -----------------------------------------------------------------------------
// Error Boundary Props & State
// -----------------------------------------------------------------------------

interface ErrorBoundaryProps {
  children: ReactNode;
  /** Custom fallback UI */
  fallback?: ReactNode;
  /** Called when an error is caught */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  /** Section name for context */
  section?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

// -----------------------------------------------------------------------------
// Error Boundary Component
// -----------------------------------------------------------------------------

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error(
      `[ErrorBoundary${this.props.section ? ` - ${this.props.section}` : ''}]`,
      error,
      errorInfo,
    );
    this.props.onError?.(error, errorInfo);
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div
          className="flex min-h-[200px] flex-col items-center justify-center rounded-lg border border-red-200 bg-red-50 p-8 dark:border-red-900 dark:bg-red-950/30"
          role="alert"
        >
          <ExclamationTriangleIcon className="h-10 w-10 text-red-500" />
          <h2 className="mt-4 text-lg font-semibold text-red-800 dark:text-red-200">
            Something went wrong
          </h2>
          <p className="mt-2 max-w-md text-center text-sm text-red-600 dark:text-red-300">
            {this.state.error?.message || 'An unexpected error occurred in this section.'}
          </p>
          {this.props.section && (
            <p className="mt-1 text-xs text-red-400">
              Section: {this.props.section}
            </p>
          )}
          <button
            onClick={this.handleReset}
            className="btn-primary mt-4"
            type="button"
          >
            Try Again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
