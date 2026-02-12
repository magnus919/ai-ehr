import { useAllergies, useDeactivateAllergy } from '@/hooks/useAllergies';
import { formatDate } from '@/utils/formatters';
import { PencilIcon, TrashIcon } from '@heroicons/react/24/outline';
import type { AllergyIntolerance } from '@/services/allergies';

interface AllergyListProps {
  patientId: string;
  onEditAllergy?: (allergy: AllergyIntolerance) => void;
}

function getCriticalityBadge(criticality?: string) {
  const styles: Record<string, string> = {
    high: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300',
    low: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300',
    unable: 'bg-gray-100 text-gray-800 dark:bg-gray-950 dark:text-gray-300',
  };

  const label = criticality || 'Unknown';
  const style = styles[criticality || 'unable'] || styles.unable;

  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}>
      {label.charAt(0).toUpperCase() + label.slice(1)}
    </span>
  );
}

function getStatusBadge(status: string) {
  const styles: Record<string, string> = {
    active: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300',
    inactive: 'bg-gray-100 text-gray-800 dark:bg-gray-950 dark:text-gray-300',
    resolved: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300',
  };

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
        styles[status] || styles.inactive
      }`}
    >
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

export function AllergyList({ patientId, onEditAllergy }: AllergyListProps) {
  const { data: allergies, isLoading } = useAllergies({ patient_id: patientId });
  const deactivateAllergy = useDeactivateAllergy();

  const handleDeactivate = async (id: string) => {
    if (confirm('Are you sure you want to deactivate this allergy?')) {
      await deactivateAllergy.mutateAsync(id);
    }
  };

  if (isLoading) {
    return (
      <div className="card">
        <p className="text-gray-500">Loading allergies...</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
        Allergies & Intolerances
      </h2>

      {!allergies || allergies.length === 0 ? (
        <p className="text-gray-500">No known allergies recorded.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  Allergen
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  Criticality
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  Recorded
                </th>
                <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
              {allergies.map((allergy) => (
                <tr key={allergy.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-gray-100">
                        {allergy.code_display}
                      </p>
                      {allergy.note && (
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {allergy.note}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                    {allergy.type}
                  </td>
                  <td className="px-4 py-3">{getCriticalityBadge(allergy.criticality)}</td>
                  <td className="px-4 py-3">{getStatusBadge(allergy.clinical_status)}</td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                    {formatDate(allergy.recorded_date)}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => onEditAllergy?.(allergy)}
                        className="text-primary-600 hover:text-primary-900 dark:text-primary-400 dark:hover:text-primary-300"
                        title="Edit"
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDeactivate(allergy.id)}
                        className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                        title="Deactivate"
                      >
                        <TrashIcon className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
