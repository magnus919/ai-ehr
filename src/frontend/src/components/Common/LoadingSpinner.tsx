import { clsx } from 'clsx';

interface LoadingSpinnerProps {
  /** Size variant */
  size?: 'sm' | 'md' | 'lg';
  /** Optional additional class names */
  className?: string;
  /** Screen reader label */
  label?: string;
}

const sizeClasses = {
  sm: 'h-4 w-4 border-2',
  md: 'h-8 w-8 border-2',
  lg: 'h-12 w-12 border-3',
};

export function LoadingSpinner({
  size = 'md',
  className,
  label = 'Loading...',
}: LoadingSpinnerProps) {
  return (
    <div className={clsx('flex items-center justify-center', className)} role="status">
      <div
        className={clsx(
          'animate-spin rounded-full border-primary-200 border-t-primary-600',
          sizeClasses[size],
        )}
      />
      <span className="sr-only">{label}</span>
    </div>
  );
}

/**
 * Full-page loading spinner, used for initial app load or page transitions.
 */
export function PageLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface dark:bg-gray-900">
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
          Loading...
        </p>
      </div>
    </div>
  );
}
