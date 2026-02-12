import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query';
import { appointmentService } from '@/services/appointments';
import type {
  AppointmentCreateInput,
  AppointmentUpdateInput,
  AppointmentSearchParams,
  UUID,
} from '@/types';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/services/api';

// -----------------------------------------------------------------------------
// Query Keys
// -----------------------------------------------------------------------------

export const appointmentKeys = {
  all: ['appointments'] as const,
  lists: () => [...appointmentKeys.all, 'list'] as const,
  list: (params?: AppointmentSearchParams) =>
    [...appointmentKeys.lists(), params] as const,
  details: () => [...appointmentKeys.all, 'detail'] as const,
  detail: (id: UUID) => [...appointmentKeys.details(), id] as const,
  today: () => [...appointmentKeys.all, 'today'] as const,
  range: (start: string, end: string, providerId?: UUID) =>
    [...appointmentKeys.all, 'range', start, end, providerId] as const,
  availability: (providerId: UUID, startDate: string, endDate: string) =>
    [...appointmentKeys.all, 'availability', providerId, startDate, endDate] as const,
};

// -----------------------------------------------------------------------------
// Queries
// -----------------------------------------------------------------------------

/**
 * Fetch a paginated list of appointments.
 */
export function useAppointments(params?: AppointmentSearchParams) {
  return useQuery({
    queryKey: appointmentKeys.list(params),
    queryFn: () => appointmentService.getAppointments(params),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

/**
 * Fetch a single appointment by ID.
 */
export function useAppointment(id: UUID | undefined) {
  return useQuery({
    queryKey: appointmentKeys.detail(id!),
    queryFn: () => appointmentService.getAppointment(id!),
    enabled: !!id,
    staleTime: 30_000,
  });
}

/**
 * Fetch today's appointments.
 */
export function useTodayAppointments() {
  return useQuery({
    queryKey: appointmentKeys.today(),
    queryFn: () => appointmentService.getTodayAppointments(),
    staleTime: 60_000,
    refetchInterval: 5 * 60_000, // Refresh every 5 minutes
  });
}

/**
 * Fetch appointments for a date range (calendar view).
 */
export function useAppointmentsForRange(
  startDate: string,
  endDate: string,
  providerId?: UUID,
) {
  return useQuery({
    queryKey: appointmentKeys.range(startDate, endDate, providerId),
    queryFn: () =>
      appointmentService.getAppointmentsForRange(startDate, endDate, providerId),
    enabled: !!startDate && !!endDate,
    staleTime: 30_000,
  });
}

/**
 * Fetch provider availability slots.
 */
export function useProviderAvailability(
  providerId: UUID | undefined,
  startDate: string,
  endDate: string,
  duration?: number,
) {
  return useQuery({
    queryKey: appointmentKeys.availability(providerId!, startDate, endDate),
    queryFn: () =>
      appointmentService.getAvailability({
        providerId: providerId!,
        startDate,
        endDate,
        duration,
      }),
    enabled: !!providerId && !!startDate && !!endDate,
    staleTime: 60_000,
  });
}

// -----------------------------------------------------------------------------
// Mutations
// -----------------------------------------------------------------------------

/**
 * Create a new appointment.
 */
export function useCreateAppointment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: AppointmentCreateInput) =>
      appointmentService.createAppointment(input),
    onSuccess: (appointment) => {
      queryClient.invalidateQueries({ queryKey: appointmentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: appointmentKeys.today() });
      queryClient.setQueryData(
        appointmentKeys.detail(appointment.id),
        appointment,
      );
      toast.success('Appointment booked successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

/**
 * Update an existing appointment.
 */
export function useUpdateAppointment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      input,
    }: {
      id: UUID;
      input: AppointmentUpdateInput;
    }) => appointmentService.updateAppointment(id, input),
    onSuccess: (appointment) => {
      queryClient.invalidateQueries({ queryKey: appointmentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: appointmentKeys.today() });
      queryClient.setQueryData(
        appointmentKeys.detail(appointment.id),
        appointment,
      );
      toast.success('Appointment updated');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

/**
 * Cancel an appointment.
 */
export function useCancelAppointment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }: { id: UUID; reason: string }) =>
      appointmentService.cancelAppointment(id, reason),
    onSuccess: (appointment) => {
      queryClient.invalidateQueries({ queryKey: appointmentKeys.lists() });
      queryClient.invalidateQueries({ queryKey: appointmentKeys.today() });
      queryClient.setQueryData(
        appointmentKeys.detail(appointment.id),
        appointment,
      );
      toast.success('Appointment cancelled');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

/**
 * Check in a patient.
 */
export function useCheckInAppointment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: UUID) => appointmentService.checkIn(id),
    onSuccess: (appointment) => {
      queryClient.invalidateQueries({ queryKey: appointmentKeys.today() });
      queryClient.setQueryData(
        appointmentKeys.detail(appointment.id),
        appointment,
      );
      toast.success('Patient checked in');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

/**
 * Mark appointment as no-show.
 */
export function useMarkNoShow() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: UUID) => appointmentService.markNoShow(id),
    onSuccess: (appointment) => {
      queryClient.invalidateQueries({ queryKey: appointmentKeys.today() });
      queryClient.setQueryData(
        appointmentKeys.detail(appointment.id),
        appointment,
      );
      toast.success('Marked as no-show');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}
