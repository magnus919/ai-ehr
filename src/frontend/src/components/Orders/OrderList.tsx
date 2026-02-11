import { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  PlusIcon,
  FunnelIcon,
  ClipboardDocumentListIcon,
} from '@heroicons/react/24/outline';
import { DataTable, type Column } from '@/components/Common/DataTable';
import { StatusBadge } from '@/components/Common/StatusBadge';
import {
  ORDER_TYPE_LABELS,
  ORDER_STATUS_LABELS,
  ORDER_STATUS_COLORS,
  ORDER_PRIORITY_LABELS,
  ORDER_PRIORITY_COLORS,
  ORDER_TYPE_OPTIONS,
  ORDER_STATUS_OPTIONS,
  DEFAULT_PAGE_SIZE,
} from '@/utils/constants';
import { formatDateTime } from '@/utils/formatters';
import type { Order, OrderType, OrderStatus } from '@/types';

// In production, this would use a useOrders hook backed by TanStack Query.
// Shown here with local state for structure.

interface OrderListProps {
  /** Orders data (passed from page or hook) */
  orders?: Order[];
  /** Loading state */
  isLoading?: boolean;
  /** Total count for pagination */
  total?: number;
}

export function OrderList({
  orders = [],
  isLoading = false,
  total = 0,
}: OrderListProps) {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('authoredOn');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [filterType, setFilterType] = useState<OrderType | ''>('');
  const [filterStatus, setFilterStatus] = useState<OrderStatus | ''>('');
  const [showFilters, setShowFilters] = useState(false);

  // Filter locally for demonstration (in production, pass to API)
  const filteredOrders = useMemo(() => {
    let result = orders;
    if (filterType) {
      result = result.filter((o) => o.type === filterType);
    }
    if (filterStatus) {
      result = result.filter((o) => o.status === filterStatus);
    }
    return result;
  }, [orders, filterType, filterStatus]);

  const columns: Column<Order>[] = useMemo(
    () => [
      {
        key: 'type',
        header: 'Type',
        sortable: true,
        render: (order) => (
          <span className="font-medium">
            {ORDER_TYPE_LABELS[order.type] ?? order.type}
          </span>
        ),
      },
      {
        key: 'code',
        header: 'Order',
        render: (order) => (
          <div>
            <p className="font-medium text-gray-900 dark:text-gray-100">
              {order.code.text ?? order.code.coding[0]?.display}
            </p>
            <p className="text-xs text-gray-500">
              {order.code.coding[0]?.code}
            </p>
          </div>
        ),
      },
      {
        key: 'patient',
        header: 'Patient',
        render: (order) => (
          <span>{order.subject.display ?? '--'}</span>
        ),
      },
      {
        key: 'priority',
        header: 'Priority',
        sortable: true,
        render: (order) => (
          <StatusBadge
            label={ORDER_PRIORITY_LABELS[order.priority] ?? order.priority}
            color={ORDER_PRIORITY_COLORS[order.priority] ?? 'gray'}
            size="sm"
          />
        ),
      },
      {
        key: 'status',
        header: 'Status',
        sortable: true,
        render: (order) => (
          <StatusBadge
            label={ORDER_STATUS_LABELS[order.status] ?? order.status}
            color={ORDER_STATUS_COLORS[order.status] ?? 'gray'}
            dot
          />
        ),
      },
      {
        key: 'authoredOn',
        header: 'Ordered',
        sortable: true,
        render: (order) => (
          <span className="text-xs">
            {formatDateTime(order.authoredOn)}
          </span>
        ),
      },
      {
        key: 'requester',
        header: 'Ordered By',
        render: (order) => (
          <span className="text-xs">
            {order.requester.display ?? '--'}
          </span>
        ),
      },
      {
        key: 'actions',
        header: 'Actions',
        srOnly: true,
        align: 'right',
        render: (order) => (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              navigate(`/orders/${order.id}`);
            }}
            className="text-primary-600 hover:text-primary-800 dark:text-primary-400"
          >
            View
          </button>
        ),
      },
    ],
    [navigate],
  );

  const handleSort = useCallback((key: string, order: 'asc' | 'desc') => {
    setSortBy(key);
    setSortOrder(order);
  }, []);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Orders
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Manage medication, laboratory, and imaging orders.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className="btn-secondary"
          >
            <FunnelIcon className="h-4 w-4" />
            Filters
          </button>
          <button
            type="button"
            onClick={() => navigate('/orders/new')}
            className="btn-primary"
          >
            <PlusIcon className="h-4 w-4" />
            New Order
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="card flex flex-wrap gap-4">
          <div>
            <label
              htmlFor="filter-order-type"
              className="block text-xs font-medium text-gray-500 dark:text-gray-400"
            >
              Order Type
            </label>
            <select
              id="filter-order-type"
              className="input-base mt-1 w-40"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as OrderType | '')}
            >
              <option value="">All Types</option>
              {ORDER_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label
              htmlFor="filter-order-status"
              className="block text-xs font-medium text-gray-500 dark:text-gray-400"
            >
              Status
            </label>
            <select
              id="filter-order-status"
              className="input-base mt-1 w-40"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as OrderStatus | '')}
            >
              <option value="">All Statuses</option>
              {ORDER_STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      {/* Table */}
      <DataTable
        columns={columns}
        data={filteredOrders}
        keyExtractor={(order) => order.id}
        isLoading={isLoading}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSort={handleSort}
        page={page}
        pageSize={DEFAULT_PAGE_SIZE}
        total={total || filteredOrders.length}
        onPageChange={setPage}
        emptyMessage="No orders found"
        emptyIcon={
          <ClipboardDocumentListIcon className="h-10 w-10 text-gray-300" />
        }
      />
    </div>
  );
}
