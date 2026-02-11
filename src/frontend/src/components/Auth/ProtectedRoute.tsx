import { Navigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import type { UserRole } from '@/types';

// -----------------------------------------------------------------------------
// Protected Route Component
// -----------------------------------------------------------------------------

interface ProtectedRouteProps {
  children: React.ReactNode;
  /** Optional: restrict to specific roles */
  allowedRoles?: UserRole[];
}

export function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const location = useLocation();

  // Not authenticated -> redirect to login
  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        state={{ from: location.pathname }}
        replace
      />
    );
  }

  // Role check
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return (
      <div
        className="flex min-h-[60vh] flex-col items-center justify-center"
        role="alert"
      >
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Access Denied
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          You do not have permission to access this page.
        </p>
        <a href="/dashboard" className="btn-primary mt-4">
          Go to Dashboard
        </a>
      </div>
    );
  }

  return <>{children}</>;
}
