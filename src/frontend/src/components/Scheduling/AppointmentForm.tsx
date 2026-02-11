import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { PatientSearch } from '@/components/Patients/PatientSearch';
import {
  APPOINTMENT_TYPE_OPTIONS,
  APPOINTMENT_DURATION_OPTIONS,
} from '@/utils/constants';
import type { Appointment, Patient } from '@/types';

// -----------------------------------------------------------------------------
// Validation Schema
// -----------------------------------------------------------------------------

const appointmentFormSchema = z.object({
  patientId: z.string().min(1, 'Patient is required'),
  patientDisplay: z.string().optional(),
  providerId: z.string().min(1, 'Provider is required'),
  appointmentType: z.string().min(1, 'Appointment type is required'),
  date: z.string().min(1, 'Date is required'),
  startTime: z.string().min(1, 'Start time is required'),
  duration: z.coerce.number().min(15, 'Duration must be at least 15 minutes'),
  reason: z.string().optional(),
  description: z.string().optional(),
  patientInstruction: z.string().optional(),
  comment: z.string().optional(),
});

type AppointmentFormData = z.infer<typeof appointmentFormSchema>;

// -----------------------------------------------------------------------------
// Component Props
// -----------------------------------------------------------------------------

interface AppointmentFormProps {
  /** Existing appointment for editing */
  appointment?: Appointment;
  /** Pre-selected date/time */
  defaultDate?: Date;
  /** Called on form submission */
  onSubmit: (data: AppointmentFormData) => void;
  /** Loading state */
  isLoading?: boolean;
  /** Called when cancel is clicked */
  onCancel?: () => void;
}

// Mock providers list (would come from API in production)
const MOCK_PROVIDERS = [
  { id: 'prov-1', name: 'Dr. Sarah Johnson' },
  { id: 'prov-2', name: 'Dr. Michael Chen' },
  { id: 'prov-3', name: 'Dr. Emily Williams' },
];

// -----------------------------------------------------------------------------
// AppointmentForm Component
// -----------------------------------------------------------------------------

export function AppointmentForm({
  appointment,
  defaultDate,
  onSubmit,
  isLoading = false,
  onCancel,
}: AppointmentFormProps) {
  const defaultDateStr = defaultDate
    ? defaultDate.toISOString().split('T')[0]
    : '';
  const defaultTimeStr = defaultDate
    ? defaultDate.toTimeString().slice(0, 5)
    : '';

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<AppointmentFormData>({
    resolver: zodResolver(appointmentFormSchema),
    defaultValues: appointment
      ? {
          patientId: appointment.patient.reference?.split('/').pop() ?? '',
          patientDisplay: appointment.patient.display ?? '',
          providerId: appointment.provider.reference?.split('/').pop() ?? '',
          appointmentType: appointment.appointmentType,
          date: appointment.start.split('T')[0],
          startTime: appointment.start.split('T')[1]?.slice(0, 5) ?? '',
          duration: appointment.minutesDuration,
          reason: appointment.reasonCode?.[0]?.text ?? '',
          description: appointment.description ?? '',
          patientInstruction: appointment.patientInstruction ?? '',
          comment: appointment.comment ?? '',
        }
      : {
          patientId: '',
          providerId: '',
          appointmentType: '',
          date: defaultDateStr,
          startTime: defaultTimeStr,
          duration: 30,
          reason: '',
        },
  });

  const selectedPatientDisplay = watch('patientDisplay');

  const handlePatientSelect = (patient: Patient) => {
    setValue('patientId', patient.id, { shouldValidate: true });
    setValue(
      'patientDisplay',
      `${patient.name.given?.[0] ?? ''} ${patient.name.family ?? ''} (MRN: ${patient.mrn})`,
    );
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
      {/* Patient Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Patient <span className="text-red-500">*</span>
        </label>
        {selectedPatientDisplay ? (
          <div className="mt-1 flex items-center gap-2">
            <span className="input-base flex-1 bg-gray-50 dark:bg-gray-700">
              {selectedPatientDisplay}
            </span>
            <button
              type="button"
              onClick={() => {
                setValue('patientId', '');
                setValue('patientDisplay', '');
              }}
              className="btn-ghost text-xs"
            >
              Change
            </button>
          </div>
        ) : (
          <div className="mt-1">
            <PatientSearch
              onSelect={handlePatientSelect}
              showAutocomplete
              placeholder="Search for a patient..."
            />
          </div>
        )}
        <input type="hidden" {...register('patientId')} />
        {errors.patientId && (
          <p className="mt-1 text-sm text-red-600" role="alert">
            {errors.patientId.message}
          </p>
        )}
      </div>

      {/* Provider Selection */}
      <div>
        <label
          htmlFor="providerId"
          className="block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          Provider <span className="text-red-500">*</span>
        </label>
        <select
          id="providerId"
          {...register('providerId')}
          className="input-base mt-1"
        >
          <option value="">Select provider</option>
          {MOCK_PROVIDERS.map((prov) => (
            <option key={prov.id} value={prov.id}>
              {prov.name}
            </option>
          ))}
        </select>
        {errors.providerId && (
          <p className="mt-1 text-sm text-red-600" role="alert">
            {errors.providerId.message}
          </p>
        )}
      </div>

      {/* Appointment Type */}
      <div>
        <label
          htmlFor="appointmentType"
          className="block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          Appointment Type <span className="text-red-500">*</span>
        </label>
        <select
          id="appointmentType"
          {...register('appointmentType')}
          className="input-base mt-1"
        >
          <option value="">Select type</option>
          {APPOINTMENT_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {errors.appointmentType && (
          <p className="mt-1 text-sm text-red-600" role="alert">
            {errors.appointmentType.message}
          </p>
        )}
      </div>

      {/* Date and Time */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <label
            htmlFor="date"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Date <span className="text-red-500">*</span>
          </label>
          <input
            id="date"
            type="date"
            {...register('date')}
            className="input-base mt-1"
            min={new Date().toISOString().split('T')[0]}
          />
          {errors.date && (
            <p className="mt-1 text-sm text-red-600" role="alert">
              {errors.date.message}
            </p>
          )}
        </div>
        <div>
          <label
            htmlFor="startTime"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Start Time <span className="text-red-500">*</span>
          </label>
          <input
            id="startTime"
            type="time"
            {...register('startTime')}
            className="input-base mt-1"
            min="07:00"
            max="18:00"
            step="900"
          />
          {errors.startTime && (
            <p className="mt-1 text-sm text-red-600" role="alert">
              {errors.startTime.message}
            </p>
          )}
        </div>
        <div>
          <label
            htmlFor="duration"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Duration
          </label>
          <select
            id="duration"
            {...register('duration')}
            className="input-base mt-1"
          >
            {APPOINTMENT_DURATION_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Reason */}
      <div>
        <label
          htmlFor="reason"
          className="block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          Reason for Visit
        </label>
        <input
          id="reason"
          {...register('reason')}
          className="input-base mt-1"
          placeholder="Brief reason for the appointment"
        />
      </div>

      {/* Patient Instructions */}
      <div>
        <label
          htmlFor="patientInstruction"
          className="block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          Patient Instructions
        </label>
        <textarea
          id="patientInstruction"
          rows={2}
          {...register('patientInstruction')}
          className="input-base mt-1"
          placeholder="Instructions for the patient (e.g., fasting requirements)"
        />
      </div>

      {/* Internal Comment */}
      <div>
        <label
          htmlFor="comment"
          className="block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          Internal Notes
        </label>
        <textarea
          id="comment"
          rows={2}
          {...register('comment')}
          className="input-base mt-1"
          placeholder="Internal notes (not visible to patient)"
        />
      </div>

      {/* Form Actions */}
      <div className="flex items-center justify-end gap-3 border-t border-gray-200 pt-4 dark:border-gray-700">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary">
            Cancel
          </button>
        )}
        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? (
            <LoadingSpinner size="sm" />
          ) : appointment ? (
            'Update Appointment'
          ) : (
            'Book Appointment'
          )}
        </button>
      </div>
    </form>
  );
}
