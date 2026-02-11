import { useEffect } from 'react';
import { DashboardPage as DashboardContent } from '@/components/Dashboard/DashboardPage';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';

/**
 * Dashboard page wrapper that sets breadcrumbs and wraps with error boundary.
 */
export default function DashboardPage() {
  const setBreadcrumbs = useUIStore((s) => s.setBreadcrumbs);

  useEffect(() => {
    setBreadcrumbs([{ label: 'Dashboard' }]);
    return () => setBreadcrumbs([]);
  }, [setBreadcrumbs]);

  return (
    <ErrorBoundary section="Dashboard">
      <DashboardContent />
    </ErrorBoundary>
  );
}
