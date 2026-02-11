import { clsx } from 'clsx';
import type { StatusColor } from '@/utils/constants';

// -----------------------------------------------------------------------------
// Status Badge Component
// -----------------------------------------------------------------------------

interface StatusBadgeProps {
  /** Status label to display */
  label: string;
  /** Color variant */
  color: StatusColor;
  /** Size variant */
  size?: 'sm' | 'md';
  /** Show a pulsing dot indicator */
  dot?: boolean;
  /** Additional class names */
  className?: string;
}

const colorClasses: Record<StatusColor, string> = {
  green:
    'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  yellow:
    'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  red: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  blue: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  gray: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  purple:
    'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
  orange:
    'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  teal: 'bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400',
};

const dotColorClasses: Record<StatusColor, string> = {
  green: 'bg-green-500',
  yellow: 'bg-yellow-500',
  red: 'bg-red-500',
  blue: 'bg-blue-500',
  gray: 'bg-gray-500',
  purple: 'bg-purple-500',
  orange: 'bg-orange-500',
  teal: 'bg-teal-500',
};

const sizeClasses = {
  sm: 'px-2 py-0.5 text-2xs',
  md: 'px-2.5 py-0.5 text-xs',
};

export function StatusBadge({
  label,
  color,
  size = 'md',
  dot = false,
  className,
}: StatusBadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full font-medium',
        colorClasses[color],
        sizeClasses[size],
        className,
      )}
    >
      {dot && (
        <span
          className={clsx(
            'h-1.5 w-1.5 rounded-full',
            dotColorClasses[color],
          )}
          aria-hidden="true"
        />
      )}
      {label}
    </span>
  );
}
