import { useEffect, useState, useCallback } from 'react';
import { Calendar } from '@/components/Scheduling/Calendar';
import { AppointmentForm } from '@/components/Scheduling/AppointmentForm';
import { Modal } from '@/components/Common/Modal';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';
import { useCreateAppointment } from '@/hooks/useAppointments';
import type { Appointment } from '@/types';

/**
 * Scheduling / Calendar page wrapper.
 */
export default function SchedulingPage() {
  const setBreadcrumbs = useUIStore((s) => s.setBreadcrumbs);
  const [showNewAppointment, setShowNewAppointment] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>();
  const [selectedAppointment, setSelectedAppointment] =
    useState<Appointment | null>(null);

  const createAppointment = useCreateAppointment();

  useEffect(() => {
    setBreadcrumbs([{ label: 'Scheduling' }]);
    return () => setBreadcrumbs([]);
  }, [setBreadcrumbs]);

  const handleSlotClick = useCallback((date: Date) => {
    setSelectedDate(date);
    setShowNewAppointment(true);
  }, []);

  const handleAppointmentClick = useCallback((appointment: Appointment) => {
    setSelectedAppointment(appointment);
  }, []);

  const handleCreateAppointment = useCallback(
    async (data: Record<string, unknown>) => {
      // Transform form data to API shape
      const input = {
        appointmentType: data.appointmentType as string,
        start: `${data.date}T${data.startTime}:00`,
        end: '', // Calculated from duration
        minutesDuration: data.duration as number,
        patientId: data.patientId as string,
        providerId: data.providerId as string,
        description: (data.description as string) || undefined,
        comment: (data.comment as string) || undefined,
        patientInstruction: (data.patientInstruction as string) || undefined,
      };
      try {
        await createAppointment.mutateAsync(input as Parameters<typeof createAppointment.mutateAsync>[0]);
        setShowNewAppointment(false);
        setSelectedDate(undefined);
      } catch {
        // Error handled by mutation
      }
    },
    [createAppointment],
  );

  return (
    <ErrorBoundary section="Scheduling">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Scheduling
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Manage appointments and provider schedules.
            </p>
          </div>
          <button
            type="button"
            onClick={() => setShowNewAppointment(true)}
            className="btn-primary"
          >
            New Appointment
          </button>
        </div>

        <Calendar
          onSlotClick={handleSlotClick}
          onAppointmentClick={handleAppointmentClick}
        />
      </div>

      {/* New Appointment Modal */}
      <Modal
        open={showNewAppointment}
        onClose={() => {
          setShowNewAppointment(false);
          setSelectedDate(undefined);
        }}
        title="New Appointment"
        size="xl"
      >
        <AppointmentForm
          defaultDate={selectedDate}
          onSubmit={handleCreateAppointment}
          isLoading={createAppointment.isPending}
          onCancel={() => {
            setShowNewAppointment(false);
            setSelectedDate(undefined);
          }}
        />
      </Modal>

      {/* Appointment Detail Modal */}
      <Modal
        open={!!selectedAppointment}
        onClose={() => setSelectedAppointment(null)}
        title="Appointment Details"
        size="lg"
      >
        {selectedAppointment && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs font-medium text-gray-500">Patient</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {selectedAppointment.patient.display}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500">Provider</p>
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {selectedAppointment.provider.display}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500">Type</p>
                <p className="text-sm text-gray-900 dark:text-gray-100">
                  {selectedAppointment.appointmentType}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500">Status</p>
                <p className="text-sm text-gray-900 dark:text-gray-100">
                  {selectedAppointment.status}
                </p>
              </div>
            </div>
            {selectedAppointment.comment && (
              <div>
                <p className="text-xs font-medium text-gray-500">Notes</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">
                  {selectedAppointment.comment}
                </p>
              </div>
            )}
          </div>
        )}
      </Modal>
    </ErrorBoundary>
  );
}
