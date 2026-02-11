import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PatientDetail } from '@/components/Patients/PatientDetail';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';
import { usePatient } from '@/hooks/usePatients';
import { formatNameLastFirst } from '@/utils/formatters';

/**
 * Patient detail page wrapper.
 */
export default function PatientDetailPage() {
  const { patientId } = useParams<{ patientId: string }>();
  const navigate = useNavigate();
  const setBreadcrumbs = useUIStore((s) => s.setBreadcrumbs);
  const { data: patient } = usePatient(patientId);

  useEffect(() => {
    const crumbs = [
      { label: 'Patients', href: '/patients' },
      {
        label: patient ? formatNameLastFirst(patient.name) : 'Loading...',
      },
    ];
    setBreadcrumbs(crumbs);
    return () => setBreadcrumbs([]);
  }, [setBreadcrumbs, patient]);

  if (!patientId) {
    navigate('/patients');
    return null;
  }

  return (
    <ErrorBoundary section="Patient Detail">
      <PatientDetail patientId={patientId} />
    </ErrorBoundary>
  );
}
