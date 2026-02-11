import { useEffect } from 'react';
import { OrderList } from '@/components/Orders/OrderList';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';

/**
 * Orders page wrapper.
 */
export default function OrdersPage() {
  const setBreadcrumbs = useUIStore((s) => s.setBreadcrumbs);

  useEffect(() => {
    setBreadcrumbs([{ label: 'Orders' }]);
    return () => setBreadcrumbs([]);
  }, [setBreadcrumbs]);

  return (
    <ErrorBoundary section="Orders">
      <OrderList />
    </ErrorBoundary>
  );
}
