import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { VitalSignsForm } from '@/components/VitalSigns/VitalSignsForm';
import { VitalSignsTrend } from '@/components/VitalSigns/VitalSignsTrend';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';

export default function VitalSignsPage() {
  const [searchParams] = useSearchParams();
  const [selectedPatientId, setSelectedPatientId] = useState<string>(
    searchParams.get('patientId') || ''
  );
  const setBreadcrumbs = useUIStore((s) => s.setBreadcrumbs);

  useEffect(() => {
    setBreadcrumbs([{ label: 'Vital Signs' }]);
    return () => setBreadcrumbs([]);
  }, [setBreadcrumbs]);

  const handleSuccess = () => {
    // Refresh the trend view
  };

  return (
    <ErrorBoundary section="Vital Signs">
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Vital Signs</h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            Record and view patient vital signs
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
          <>
            <VitalSignsForm patientId={selectedPatientId} onSuccess={handleSuccess} />
            <VitalSignsTrend patientId={selectedPatientId} />
          </>
        )}
      </div>
    </ErrorBoundary>
  );
}
