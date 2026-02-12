import { useState, useEffect } from 'react';
import { useUpdateUser } from '@/hooks/useUsers';
import type { User, UserUpdate } from '@/services/users';

interface UserFormProps {
  user: User;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Admin' },
  { value: 'physician', label: 'Physician' },
  { value: 'nurse', label: 'Nurse' },
  { value: 'medical_assistant', label: 'Medical Assistant' },
  { value: 'front_desk', label: 'Front Desk' },
  { value: 'billing', label: 'Billing' },
  { value: 'lab_tech', label: 'Lab Tech' },
  { value: 'pharmacist', label: 'Pharmacist' },
];

export function UserForm({ user, onSuccess, onCancel }: UserFormProps) {
  const [formData, setFormData] = useState<UserUpdate>({
    first_name: user.first_name,
    last_name: user.last_name,
    role: user.role,
    npi: user.npi,
    is_active: user.is_active,
  });

  const updateUser = useUpdateUser();

  useEffect(() => {
    setFormData({
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role,
      npi: user.npi,
      is_active: user.is_active,
    });
  }, [user]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await updateUser.mutateAsync({ id: user.id, input: formData });
    if (onSuccess) onSuccess();
  };

  const handleChange = (field: keyof UserUpdate, value: string | boolean) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="card space-y-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Edit User</h2>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            First Name
          </label>
          <input
            type="text"
            value={formData.first_name}
            onChange={(e) => handleChange('first_name', e.target.value)}
            required
            className="input-base mt-1"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Last Name
          </label>
          <input
            type="text"
            value={formData.last_name}
            onChange={(e) => handleChange('last_name', e.target.value)}
            required
            className="input-base mt-1"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Role
          </label>
          <select
            value={formData.role}
            onChange={(e) => handleChange('role', e.target.value)}
            required
            className="input-base mt-1"
          >
            {ROLE_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            NPI (optional)
          </label>
          <input
            type="text"
            value={formData.npi || ''}
            onChange={(e) => handleChange('npi', e.target.value)}
            className="input-base mt-1"
            placeholder="10-digit NPI"
          />
        </div>
      </div>

      <div>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={formData.is_active}
            onChange={(e) => handleChange('is_active', e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          <span className="text-sm text-gray-700 dark:text-gray-300">Active User</span>
        </label>
      </div>

      <div className="flex justify-end gap-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary">
            Cancel
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={updateUser.isPending}>
          {updateUser.isPending ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </form>
  );
}
