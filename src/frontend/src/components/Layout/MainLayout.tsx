import { Outlet, Link } from 'react-router-dom';
import { clsx } from 'clsx';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';
import { useAuthStore } from '@/store/authStore';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/20/solid';
import { Modal } from '@/components/Common/Modal';

// -----------------------------------------------------------------------------
// Main Layout Component
// -----------------------------------------------------------------------------

export function MainLayout() {
  const sidebarCollapsed = useUIStore((s) => s.sidebarCollapsed);
  const breadcrumbs = useUIStore((s) => s.breadcrumbs);
  const sessionWarningVisible = useAuthStore((s) => s.sessionWarningVisible);
  const updateLastActivity = useAuthStore((s) => s.updateLastActivity);
  const setSessionWarning = useAuthStore((s) => s.setSessionWarning);
  const logout = useAuthStore((s) => s.logout);

  return (
    <div className="min-h-screen bg-surface dark:bg-gray-900">
      {/* Skip to main content link */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      {/* Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div
        className={clsx(
          'flex min-h-screen flex-col transition-all duration-300',
          sidebarCollapsed
            ? 'lg:ml-sidebar-collapsed'
            : 'lg:ml-sidebar',
        )}
      >
        {/* Header */}
        <Header />

        {/* Breadcrumbs */}
        {breadcrumbs.length > 0 && (
          <nav
            className="border-b border-gray-200 bg-white px-4 py-2 dark:border-gray-700 dark:bg-gray-800 sm:px-6"
            aria-label="Breadcrumb"
          >
            <ol className="flex items-center gap-1 text-sm">
              <li>
                <Link
                  to="/dashboard"
                  className="text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                  aria-label="Home"
                >
                  <HomeIcon className="h-4 w-4" />
                </Link>
              </li>
              {breadcrumbs.map((crumb, index) => (
                <li key={index} className="flex items-center gap-1">
                  <ChevronRightIcon
                    className="h-4 w-4 text-gray-400"
                    aria-hidden="true"
                  />
                  {crumb.href && index < breadcrumbs.length - 1 ? (
                    <Link
                      to={crumb.href}
                      className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                    >
                      {crumb.label}
                    </Link>
                  ) : (
                    <span
                      className="font-medium text-gray-900 dark:text-gray-100"
                      aria-current="page"
                    >
                      {crumb.label}
                    </span>
                  )}
                </li>
              ))}
            </ol>
          </nav>
        )}

        {/* Page Content */}
        <main id="main-content" className="flex-1 p-4 sm:p-6" tabIndex={-1}>
          <ErrorBoundary section="Main Content">
            <Outlet />
          </ErrorBoundary>
        </main>

        {/* Footer */}
        <footer className="border-t border-gray-200 bg-white px-6 py-3 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-center text-xs text-gray-400 dark:text-gray-500">
            OpenMedRecord v1.0.0 &mdash; Open Source EHR System
          </p>
        </footer>
      </div>

      {/* Session Timeout Warning Modal */}
      <Modal
        open={sessionWarningVisible}
        onClose={() => setSessionWarning(false)}
        title="Session Expiring"
        size="sm"
        showCloseButton={false}
        footer={
          <>
            <button
              type="button"
              className="btn-secondary"
              onClick={() => {
                logout();
                window.location.href = '/login';
              }}
            >
              Sign Out
            </button>
            <button
              type="button"
              className="btn-primary"
              onClick={() => {
                updateLastActivity();
                setSessionWarning(false);
              }}
            >
              Stay Signed In
            </button>
          </>
        }
      >
        <p className="text-sm text-gray-600 dark:text-gray-300">
          Your session is about to expire due to inactivity. Would you like to
          stay signed in?
        </p>
      </Modal>
    </div>
  );
}
