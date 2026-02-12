import { useNavigate } from 'react-router-dom';
import {
  CalendarDaysIcon,
  UserGroupIcon,
  ClipboardDocumentListIcon,
  ExclamationCircleIcon,
  PlusIcon,
  ArrowRightIcon,
  ClockIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useTodayAppointments } from '@/hooks/useAppointments';
import { useAuthStore } from '@/store/authStore';
import { formatTime } from '@/utils/formatters';
import {
  APPOINTMENT_STATUS_LABELS,
  APPOINTMENT_STATUS_COLORS,
  APPOINTMENT_TYPE_LABELS,
} from '@/utils/constants';

// -----------------------------------------------------------------------------
// DashboardPage Component
// -----------------------------------------------------------------------------

export function DashboardPage() {
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const { data: todayAppointments, isLoading: appointmentsLoading } =
    useTodayAppointments();

  const stats = [
    {
      name: "Today's Appointments",
      value: todayAppointments?.length ?? '--',
      icon: CalendarDaysIcon,
      color: 'text-blue-600 bg-blue-100 dark:text-blue-400 dark:bg-blue-900/30',
      href: '/scheduling',
    },
    {
      name: 'Checked In',
      value:
        todayAppointments?.filter(
          (a) => a.status === 'checked-in' || a.status === 'arrived',
        ).length ?? '--',
      icon: CheckCircleIcon,
      color: 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/30',
      href: '/scheduling',
    },
    {
      name: 'Pending Orders',
      value: '--',
      icon: ClipboardDocumentListIcon,
      color: 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/30',
      href: '/orders',
    },
    {
      name: 'Critical Alerts',
      value: 0,
      icon: ExclamationCircleIcon,
      color: 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/30',
      href: '#',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Good{' '}
          {new Date().getHours() < 12
            ? 'morning'
            : new Date().getHours() < 17
              ? 'afternoon'
              : 'evening'}
          , {user?.firstName ?? 'Doctor'}
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Here&apos;s your overview for today,{' '}
          {new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
          .
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <button
            key={stat.name}
            type="button"
            onClick={() => navigate(stat.href)}
            className="card flex items-center gap-4 transition-shadow hover:shadow-md"
          >
            <div
              className={clsx(
                'flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg',
                stat.color,
              )}
            >
              <stat.icon className="h-6 w-6" />
            </div>
            <div className="text-left">
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stat.value}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {stat.name}
              </p>
            </div>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Today's Schedule */}
        <div className="card lg:col-span-2">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Today&apos;s Schedule
            </h2>
            <button
              type="button"
              onClick={() => navigate('/scheduling')}
              className="btn-ghost text-xs"
            >
              View all
              <ArrowRightIcon className="h-3 w-3" />
            </button>
          </div>

          <ErrorBoundary section="Today's Schedule">
            {appointmentsLoading ? (
              <LoadingSpinner className="py-8" />
            ) : !todayAppointments || todayAppointments.length === 0 ? (
              <div className="py-8 text-center">
                <CalendarDaysIcon className="mx-auto h-10 w-10 text-gray-300 dark:text-gray-600" />
                <p className="mt-2 text-sm text-gray-500">
                  No appointments scheduled for today.
                </p>
              </div>
            ) : (
              <div className="mt-4 divide-y divide-gray-200 dark:divide-gray-700">
                {todayAppointments.slice(0, 8).map((apt) => (
                  <button
                    key={apt.id}
                    type="button"
                    onClick={() => navigate(`/scheduling?appointment=${apt.id}`)}
                    className="flex w-full items-center gap-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-750"
                  >
                    <div className="flex w-16 flex-shrink-0 flex-col items-center">
                      <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                        {formatTime(apt.start)}
                      </span>
                      <span className="text-2xs text-gray-400">
                        {apt.minutesDuration}min
                      </span>
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {apt.patient.display ?? 'Unknown Patient'}
                      </p>
                      <p className="text-xs text-gray-500">
                        {APPOINTMENT_TYPE_LABELS[apt.appointmentType]} &middot;{' '}
                        {apt.description ?? apt.reasonCode?.[0]?.text ?? ''}
                      </p>
                    </div>
                    <StatusBadge
                      label={
                        APPOINTMENT_STATUS_LABELS[apt.status] ?? apt.status
                      }
                      color={
                        APPOINTMENT_STATUS_COLORS[apt.status] ?? 'gray'
                      }
                      size="sm"
                    />
                  </button>
                ))}
              </div>
            )}
          </ErrorBoundary>
        </div>

        {/* Quick Actions */}
        <div className="space-y-6">
          {/* Quick Actions Card */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Quick Actions
            </h2>
            <div className="mt-4 space-y-2">
              <button
                type="button"
                onClick={() => navigate('/patients/new')}
                className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                <PlusIcon className="h-5 w-5 text-primary-500" />
                Register New Patient
              </button>
              <button
                type="button"
                onClick={() => navigate('/scheduling?action=new')}
                className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                <CalendarDaysIcon className="h-5 w-5 text-secondary-500" />
                Schedule Appointment
              </button>
              <button
                type="button"
                onClick={() => navigate('/orders/new')}
                className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                <ClipboardDocumentListIcon className="h-5 w-5 text-accent-500" />
                Create Order
              </button>
              <button
                type="button"
                onClick={() => navigate('/patients')}
                className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
              >
                <UserGroupIcon className="h-5 w-5 text-gray-500" />
                Find Patient
              </button>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="card">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Recent Activity
            </h2>
            <div className="mt-4 space-y-3">
              <div className="flex items-start gap-3">
                <ClockIcon className="mt-0.5 h-4 w-4 flex-shrink-0 text-gray-400" />
                <div>
                  <p className="text-sm text-gray-700 dark:text-gray-300">
                    No recent activity to display.
                  </p>
                  <p className="text-2xs text-gray-400">
                    Activity will appear here as you work.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
