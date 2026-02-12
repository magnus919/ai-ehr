import { useObservations } from '@/hooks/useObservations';
import { formatDate } from '@/utils/formatters';

interface VitalSignsTrendProps {
  patientId: string;
}

type VitalStatus = 'normal' | 'warning' | 'critical';

const NORMAL_RANGES = {
  '8867-4': { min: 60, max: 100, critical: { min: 40, max: 140 } }, // Heart Rate
  '8480-6': { min: 90, max: 120, critical: { min: 70, max: 180 } }, // Systolic BP
  '8462-4': { min: 60, max: 80, critical: { min: 40, max: 110 } }, // Diastolic BP
  '8310-5': { min: 97.0, max: 99.0, critical: { min: 95.0, max: 103.0 } }, // Temperature
  '9279-1': { min: 12, max: 20, critical: { min: 8, max: 30 } }, // Respiratory Rate
  '2708-6': { min: 95, max: 100, critical: { min: 90, max: 100 } }, // SpO2
};

function getVitalStatus(value: number, code: string): VitalStatus {
  const range = NORMAL_RANGES[code as keyof typeof NORMAL_RANGES];
  if (!range) return 'normal';
  if (value < range.critical.min || value > range.critical.max) return 'critical';
  if (value < range.min || value > range.max) return 'warning';
  return 'normal';
}

function getStatusBadge(status: VitalStatus): JSX.Element {
  const styles = {
    normal: 'bg-green-100 text-green-800 dark:bg-green-950 dark:text-green-300',
    warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-950 dark:text-yellow-300',
    critical: 'bg-red-100 text-red-800 dark:bg-red-950 dark:text-red-300',
  };

  return (
    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ${styles[status]}`}>
      {status === 'normal' ? '✓' : status === 'warning' ? '⚠' : '⚠'}
    </span>
  );
}

export function VitalSignsTrend({ patientId }: VitalSignsTrendProps) {
  const { data: observations, isLoading } = useObservations({ patient_id: patientId });

  if (isLoading) {
    return (
      <div className="card">
        <p className="text-gray-500">Loading vital signs...</p>
      </div>
    );
  }

  if (!observations || observations.length === 0) {
    return (
      <div className="card">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
          Vital Signs Trend
        </h2>
        <p className="mt-4 text-gray-500">No vital signs recorded yet.</p>
      </div>
    );
  }

  const groupedByDate = observations.reduce((acc, obs) => {
    const date = obs.effective_date.split('T')[0];
    if (!acc[date]) acc[date] = [];
    acc[date].push(obs);
    return acc;
  }, {} as Record<string, typeof observations>);

  const sortedDates = Object.keys(groupedByDate).sort((a, b) => b.localeCompare(a));

  return (
    <div className="card space-y-4">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
        Vital Signs Trend
      </h2>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Vital Sign
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Value
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                Status
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
            {sortedDates.slice(0, 10).map((date) =>
              groupedByDate[date].map((obs, idx) => {
                const value = obs.value_numeric ?? parseFloat(obs.value_string ?? '0');
                const status = getVitalStatus(value, obs.code);

                return (
                  <tr key={`${date}-${obs.id}-${idx}`}>
                    {idx === 0 && (
                      <td
                        className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100"
                        rowSpan={groupedByDate[date].length}
                      >
                        {formatDate(date)}
                      </td>
                    )}
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                      {obs.display}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-gray-100">
                      {value} {obs.unit}
                    </td>
                    <td className="px-4 py-3">{getStatusBadge(status)}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
