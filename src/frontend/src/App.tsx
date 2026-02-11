import { lazy, Suspense } from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import { MainLayout } from '@/components/Layout/MainLayout';
import { ProtectedRoute } from '@/components/Auth/ProtectedRoute';
import { PageLoader } from '@/components/Common/LoadingSpinner';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';

// ---------------------------------------------------------------------------
// Lazy-loaded Pages
// ---------------------------------------------------------------------------

const LoginPage = lazy(() => import('@/pages/LoginPage'));
const DashboardPage = lazy(() => import('@/pages/DashboardPage'));
const PatientsPage = lazy(() => import('@/pages/PatientsPage'));
const PatientDetailPage = lazy(() => import('@/pages/PatientDetailPage'));
const SchedulingPage = lazy(() => import('@/pages/SchedulingPage'));
const OrdersPage = lazy(() => import('@/pages/OrdersPage'));

// ---------------------------------------------------------------------------
// App Component
// ---------------------------------------------------------------------------

export default function App() {
  return (
    <ErrorBoundary section="Application Root">
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<LoginPage />} />

            {/* Protected Routes with Main Layout */}
            <Route
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />

              {/* Patients */}
              <Route path="/patients" element={<PatientsPage />} />
              <Route
                path="/patients/:patientId"
                element={<PatientDetailPage />}
              />

              {/* Encounters */}
              <Route
                path="/encounters/:encounterId"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <div className="card">
                      <p className="text-gray-500">Encounter detail page - to be implemented.</p>
                    </div>
                  </Suspense>
                }
              />

              {/* Scheduling */}
              <Route path="/scheduling" element={<SchedulingPage />} />

              {/* Orders */}
              <Route path="/orders" element={<OrdersPage />} />
              <Route
                path="/orders/new"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <div className="card">
                      <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                        New Order
                      </h1>
                      <p className="mt-2 text-gray-500">
                        Order entry form page - to be implemented.
                      </p>
                    </div>
                  </Suspense>
                }
              />
              <Route
                path="/orders/:orderId"
                element={
                  <Suspense fallback={<PageLoader />}>
                    <div className="card">
                      <p className="text-gray-500">Order detail page - to be implemented.</p>
                    </div>
                  </Suspense>
                }
              />

              {/* Reports */}
              <Route
                path="/reports"
                element={
                  <div className="card">
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                      Reports
                    </h1>
                    <p className="mt-2 text-gray-500">
                      Reporting module - coming soon.
                    </p>
                  </div>
                }
              />

              {/* Admin */}
              <Route
                path="/admin"
                element={
                  <div className="card">
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                      Administration
                    </h1>
                    <p className="mt-2 text-gray-500">
                      Admin panel - coming soon.
                    </p>
                  </div>
                }
              />

              {/* Profile & Settings */}
              <Route
                path="/profile"
                element={
                  <div className="card">
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                      My Profile
                    </h1>
                    <p className="mt-2 text-gray-500">
                      User profile page - coming soon.
                    </p>
                  </div>
                }
              />
              <Route
                path="/settings"
                element={
                  <div className="card">
                    <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                      Settings
                    </h1>
                    <p className="mt-2 text-gray-500">
                      Settings page - coming soon.
                    </p>
                  </div>
                }
              />
            </Route>

            {/* Redirects */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route
              path="*"
              element={
                <div className="flex min-h-screen items-center justify-center">
                  <div className="text-center">
                    <h1 className="text-6xl font-bold text-gray-300 dark:text-gray-600">
                      404
                    </h1>
                    <p className="mt-4 text-lg text-gray-600 dark:text-gray-400">
                      Page not found
                    </p>
                    <a href="/dashboard" className="btn-primary mt-6 inline-flex">
                      Go to Dashboard
                    </a>
                  </div>
                </div>
              }
            />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </ErrorBoundary>
  );
}
