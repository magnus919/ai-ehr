import { useState, useMemo, useCallback } from 'react';
import { useUsers } from '@/hooks/useUsers';
import { formatDate } from '@/utils/formatters';
import { FunnelIcon, PencilIcon } from '@heroicons/react/24/outline';
import type { User } from '@/services/users';

interface UserListProps {
  onEditUser?: (user: User) => void;
}

const ROLE_LABELS: Record<string, string> = {
  admin: 'Admin',
  physician: 'Physician',
  nurse: 'Nurse',
  medical_assistant: 'Medical Assistant',
  front_desk: 'Front Desk',
  billing: 'Billing',
  lab_tech: 'Lab Tech',
  pharmacist: 'Pharmacist',
};

export function UserList({ onEditUser }: UserListProps) {
  const [showFilters, setShowFilters] = useState(false);
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<string>('');

  const params = useMemo(() => {
    const p: Record<string, string> = {};
    if (roleFilter) p.role = roleFilter;
    if (activeFilter) p.is_active = activeFilter;
    return p;
  }, [roleFilter, activeFilter]);

  const { data: users, isLoading } = useUsers(params);

  const handleResetFilters = useCallback(() => {
    setRoleFilter('');
    setActiveFilter('');
  }, []);

  if (isLoading) {
    return (
      <div className="card">
        <p className="text-gray-500">Loading users...</p>
      </div>
    );
  }

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Users</h2>
        <button
          type="button"
          onClick={() => setShowFilters(!showFilters)}
          className="btn-secondary"
        >
          <FunnelIcon className="h-4 w-4" />
          Filters
        </button>
      </div>

      {showFilters && (
        <div className="flex flex-wrap gap-4 border-t border-gray-200 pt-4 dark:border-gray-700">
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">
              Role
            </label>
            <select
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
              className="input-base mt-1 w-40"
            >
              <option value="">All Roles</option>
              {Object.entries(ROLE_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">
              Status
            </label>
            <select
              value={activeFilter}
              onChange={(e) => setActiveFilter(e.target.value)}
              className="input-base mt-1 w-32"
            >
              <option value="">All</option>
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>

          <div className="flex items-end">
            <button onClick={handleResetFilters} className="btn-secondary">
              Reset
            </button>
          </div>
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Name
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Email
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Role
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Status
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Last Login
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
            {users?.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">
                  {user.first_name} {user.last_name}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                  {user.email}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                  {ROLE_LABELS[user.role] || user.role}
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      user.is_active
                        ? 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-950 dark:text-gray-300'
                    }`}
                  >
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  {user.last_login ? formatDate(user.last_login) : 'Never'}
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => onEditUser?.(user)}
                    className="inline-flex items-center gap-1 text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                  >
                    <PencilIcon className="h-4 w-4" />
                    Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {(!users || users.length === 0) && (
        <p className="py-8 text-center text-gray-500">No users found.</p>
      )}
    </div>
  );
}
