import { Navigate } from 'react-router-dom';
import { LoginForm } from '@/components/Auth/LoginForm';
import { useAuthStore } from '@/store/authStore';

/**
 * Login page with centered form.
 * Redirects authenticated users to the dashboard.
 */
export default function LoginPage() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-primary-50 via-white to-secondary-50 px-4 dark:from-gray-900 dark:via-gray-900 dark:to-gray-800">
      <div className="w-full max-w-sm">
        <LoginForm />
      </div>
    </div>
  );
}
