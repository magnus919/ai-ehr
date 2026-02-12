import { useState, useEffect } from 'react';
import { UserList } from '@/components/Users/UserList';
import { UserForm } from '@/components/Users/UserForm';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';
import type { User } from '@/services/users';

export default function UserManagementPage() {
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const setBreadcrumbs = useUIStore((s) => s.setBreadcrumbs);

  useEffect(() => {
    setBreadcrumbs([{ label: 'User Management' }]);
    return () => setBreadcrumbs([]);
  }, [setBreadcrumbs]);

  const handleEditUser = (user: User) => {
    setSelectedUser(user);
  };

  const handleSuccess = () => {
    setSelectedUser(null);
  };

  const handleCancel = () => {
    setSelectedUser(null);
  };

  return (
    <ErrorBoundary section="User Management">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            User Management
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Manage system users and their roles
          </p>
        </div>

        {selectedUser && (
          <UserForm user={selectedUser} onSuccess={handleSuccess} onCancel={handleCancel} />
        )}

        <UserList onEditUser={handleEditUser} />
      </div>
    </ErrorBoundary>
  );
}
