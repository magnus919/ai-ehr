import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useImmunizations } from '@/hooks/useImmunizations';
import { formatDate } from '@/utils/formatters';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';

export default function ImmunizationsPage() {
  const [searchParams] = useSearchParams();
  const [selectedPatientId, setSelectedPatientId] = useState<string>(
    searchParams.get('patientId') || ''
  );

  const { data: immunizations, isLoading } = useImmunizations(
    selectedPatientId ? { patient_id: selectedPatientId } : undefined
  );

  const setBreadcrumbs = useUIStore((s) => s.setBreadcrumbs);

  useEffect(() => {
    setBreadcrumbs([{ label: 'Immunizations' }]);
    return () => setBreadcrumbs([]);
  }, [setBreadcrumbs]);

  return (
    <ErrorBoundary section="Immunizations">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Immunization Records
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            View patient immunization history
          </p>
        </div>

        {!selectedPatientId && (
          <div className="card">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Select Patient
            </label>
            <input
              type="text"
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              placeholder="Enter patient ID"
              className="input-base mt-1"
            />
          </div>
        )}

        {selectedPatientId && (
          <div className="card">
            <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-white">
              Immunization History
            </h2>

            {isLoading ? (
              <p className="text-gray-500">Loading immunizations...</p>
            ) : !immunizations || immunizations.length === 0 ? (
              <p className="text-gray-500">No immunizations recorded.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                        Vaccine
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                        Date Given
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                        Lot Number
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                        Route
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
                    {immunizations.map((immunization) => (
                      <tr key={immunization.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                        <td className="px-4 py-3">
                          <div>
                            <p className="font-medium text-gray-900 dark:text-gray-100">
                              {immunization.vaccine_display}
                            </p>
                            {immunization.note && (
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                {immunization.note}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                          {formatDate(immunization.occurrence_datetime)}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                              immunization.status === 'completed'
                                ? 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300'
                                : 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300'
                            }`}
                          >
                            {immunization.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                          {immunization.lot_number || '--'}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                          {immunization.route_code || '--'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
