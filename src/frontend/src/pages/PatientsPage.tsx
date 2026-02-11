import { useEffect } from 'react';
import { PatientList } from '@/components/Patients/PatientList';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';

/**
 * Patients list page wrapper.
 */
export default function PatientsPage() {
  const setBreadcrumbs = useUIStore((s) => s.setBreadcrumbs);

  useEffect(() => {
    setBreadcrumbs([{ label: 'Patients' }]);
    return () => setBreadcrumbs([]);
  }, [setBreadcrumbs]);

  return (
    <ErrorBoundary section="Patients">
      <PatientList />
    </ErrorBoundary>
  );
}
