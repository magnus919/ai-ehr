import { useState, useCallback, type ReactNode } from 'react';
import {
  ChevronUpIcon,
  ChevronDownIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
} from '@heroicons/react/20/solid';
import { clsx } from 'clsx';
import { LoadingSpinner } from './LoadingSpinner';

// -----------------------------------------------------------------------------
// DataTable Types
// -----------------------------------------------------------------------------

export interface Column<T> {
  /** Unique key for the column */
  key: string;
  /** Column header label */
  header: string;
  /** Render function for cell content */
  render: (row: T, index: number) => ReactNode;
  /** Whether this column is sortable */
  sortable?: boolean;
  /** Column width class */
  width?: string;
  /** Column alignment */
  align?: 'left' | 'center' | 'right';
  /** Screen reader only header (visually hidden) */
  srOnly?: boolean;
}

interface DataTableProps<T> {
  /** Column definitions */
  columns: Column<T>[];
  /** Data rows */
  data: T[];
  /** Unique key extractor for each row */
  keyExtractor: (row: T, index: number) => string;
  /** Loading state */
  isLoading?: boolean;
  /** Currently sorted column key */
  sortBy?: string;
  /** Current sort direction */
  sortOrder?: 'asc' | 'desc';
  /** Called when sort changes */
  onSort?: (key: string, order: 'asc' | 'desc') => void;
  /** Row click handler */
  onRowClick?: (row: T) => void;
  /** Current page (1-indexed) */
  page?: number;
  /** Items per page */
  pageSize?: number;
  /** Total number of items */
  total?: number;
  /** Called when page changes */
  onPageChange?: (page: number) => void;
  /** Empty state message */
  emptyMessage?: string;
  /** Empty state icon */
  emptyIcon?: ReactNode;
  /** Additional class names for the table wrapper */
  className?: string;
  /** Whether rows are selectable */
  striped?: boolean;
}

// -----------------------------------------------------------------------------
// DataTable Component
// -----------------------------------------------------------------------------

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  isLoading = false,
  sortBy,
  sortOrder = 'asc',
  onSort,
  onRowClick,
  page = 1,
  pageSize = 20,
  total,
  onPageChange,
  emptyMessage = 'No data found',
  emptyIcon,
  className,
  striped = true,
}: DataTableProps<T>) {
  const handleSort = useCallback(
    (key: string) => {
      if (!onSort) return;
      const newOrder =
        sortBy === key && sortOrder === 'asc' ? 'desc' : 'asc';
      onSort(key, newOrder);
    },
    [sortBy, sortOrder, onSort],
  );

  const totalPages = total ? Math.ceil(total / pageSize) : 1;
  const showPagination = total != null && total > pageSize && onPageChange;

  return (
    <div
      className={clsx('overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700', className)}
    >
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          {/* Header */}
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  className={clsx(
                    'px-6 py-3 text-xs font-medium uppercase tracking-wider',
                    col.srOnly ? 'sr-only' : '',
                    col.align === 'center'
                      ? 'text-center'
                      : col.align === 'right'
                        ? 'text-right'
                        : 'text-left',
                    col.sortable
                      ? 'cursor-pointer select-none hover:bg-gray-100 dark:hover:bg-gray-750'
                      : '',
                    'text-gray-500 dark:text-gray-400',
                    col.width,
                  )}
                  onClick={col.sortable ? () => handleSort(col.key) : undefined}
                  aria-sort={
                    sortBy === col.key
                      ? sortOrder === 'asc'
                        ? 'ascending'
                        : 'descending'
                      : undefined
                  }
                >
                  <div className="flex items-center gap-1">
                    <span>{col.header}</span>
                    {col.sortable && sortBy === col.key && (
                      <span className="ml-1">
                        {sortOrder === 'asc' ? (
                          <ChevronUpIcon className="h-4 w-4" />
                        ) : (
                          <ChevronDownIcon className="h-4 w-4" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          {/* Body */}
          <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
            {isLoading ? (
              <tr>
                <td colSpan={columns.length} className="px-6 py-12">
                  <LoadingSpinner className="mx-auto" />
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-6 py-12 text-center"
                >
                  <div className="flex flex-col items-center gap-2">
                    {emptyIcon}
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {emptyMessage}
                    </p>
                  </div>
                </td>
              </tr>
            ) : (
              data.map((row, index) => (
                <tr
                  key={keyExtractor(row, index)}
                  className={clsx(
                    onRowClick
                      ? 'cursor-pointer hover:bg-primary-50 dark:hover:bg-primary-950/20'
                      : '',
                    striped && index % 2 === 1
                      ? 'bg-gray-50/50 dark:bg-gray-800/50'
                      : '',
                    'transition-colors',
                  )}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  tabIndex={onRowClick ? 0 : undefined}
                  onKeyDown={
                    onRowClick
                      ? (e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            onRowClick(row);
                          }
                        }
                      : undefined
                  }
                  role={onRowClick ? 'button' : undefined}
                >
                  {columns.map((col) => (
                    <td
                      key={col.key}
                      className={clsx(
                        'whitespace-nowrap px-6 py-4 text-sm',
                        col.align === 'center'
                          ? 'text-center'
                          : col.align === 'right'
                            ? 'text-right'
                            : 'text-left',
                        'text-gray-900 dark:text-gray-100',
                      )}
                    >
                      {col.render(row, index)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {showPagination && (
        <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 dark:border-gray-700 dark:bg-gray-900 sm:px-6">
          <div className="flex flex-1 items-center justify-between sm:hidden">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              className="btn-secondary"
              aria-label="Previous page"
            >
              Previous
            </button>
            <span className="text-sm text-gray-700 dark:text-gray-300">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              className="btn-secondary"
              aria-label="Next page"
            >
              Next
            </button>
          </div>
          <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              Showing{' '}
              <span className="font-medium">
                {(page - 1) * pageSize + 1}
              </span>{' '}
              to{' '}
              <span className="font-medium">
                {Math.min(page * pageSize, total)}
              </span>{' '}
              of <span className="font-medium">{total}</span> results
            </p>
            <nav
              className="inline-flex -space-x-px rounded-md shadow-sm"
              aria-label="Pagination"
            >
              <button
                onClick={() => onPageChange(page - 1)}
                disabled={page <= 1}
                className="relative inline-flex items-center rounded-l-md border border-gray-300 bg-white px-2 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
                aria-label="Previous page"
              >
                <ChevronLeftIcon className="h-5 w-5" />
              </button>
              {generatePageNumbers(page, totalPages).map((pageNum, i) =>
                pageNum === '...' ? (
                  <span
                    key={`ellipsis-${i}`}
                    className="relative inline-flex items-center border border-gray-300 bg-white px-4 py-2 text-sm text-gray-700 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400"
                  >
                    ...
                  </span>
                ) : (
                  <button
                    key={pageNum}
                    onClick={() => onPageChange(pageNum as number)}
                    className={clsx(
                      'relative inline-flex items-center border px-4 py-2 text-sm font-medium',
                      pageNum === page
                        ? 'z-10 border-primary-500 bg-primary-50 text-primary-600 dark:border-primary-400 dark:bg-primary-950/30 dark:text-primary-400'
                        : 'border-gray-300 bg-white text-gray-500 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700',
                    )}
                    aria-current={pageNum === page ? 'page' : undefined}
                  >
                    {pageNum}
                  </button>
                ),
              )}
              <button
                onClick={() => onPageChange(page + 1)}
                disabled={page >= totalPages}
                className="relative inline-flex items-center rounded-r-md border border-gray-300 bg-white px-2 py-2 text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700"
                aria-label="Next page"
              >
                <ChevronRightIcon className="h-5 w-5" />
              </button>
            </nav>
          </div>
        </div>
      )}
    </div>
  );
}

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

function generatePageNumbers(
  current: number,
  total: number,
): (number | '...')[] {
  if (total <= 7) {
    return Array.from({ length: total }, (_, i) => i + 1);
  }

  const pages: (number | '...')[] = [1];

  if (current > 3) {
    pages.push('...');
  }

  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);

  for (let i = start; i <= end; i++) {
    pages.push(i);
  }

  if (current < total - 2) {
    pages.push('...');
  }

  pages.push(total);

  return pages;
}
