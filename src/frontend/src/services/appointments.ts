import api from './api';
import type {
  Appointment,
  AppointmentCreateInput,
  AppointmentUpdateInput,
  AppointmentSearchParams,
  UUID,
} from '@/types';
import type { PaginatedResponse, AvailabilitySlot } from '@/types/api';

// -----------------------------------------------------------------------------
// Appointment API Service
// -----------------------------------------------------------------------------

export const appointmentService = {
  /**
   * Get a paginated list of appointments.
   */
  async getAppointments(
    params?: AppointmentSearchParams,
  ): Promise<PaginatedResponse<Appointment>> {
    const { data } = await api.get<PaginatedResponse<Appointment>>(
      '/appointments',
      { params },
    );
    return data;
  },

  /**
   * Get a single appointment by ID.
   */
  async getAppointment(id: UUID): Promise<Appointment> {
    const { data } = await api.get<Appointment>(`/appointments/${id}`);
    return data;
  },

  /**
   * Create a new appointment.
   */
  async createAppointment(input: AppointmentCreateInput): Promise<Appointment> {
    const { data } = await api.post<Appointment>('/appointments', input);
    return data;
  },

  /**
   * Update an existing appointment.
   */
  async updateAppointment(
    id: UUID,
    input: AppointmentUpdateInput,
  ): Promise<Appointment> {
    const { data } = await api.put<Appointment>(`/appointments/${id}`, input);
    return data;
  },

  /**
   * Cancel an appointment.
   */
  async cancelAppointment(id: UUID, reason: string): Promise<Appointment> {
    const { data } = await api.post<Appointment>(`/appointments/${id}/cancel`, {
      reason,
    });
    return data;
  },

  /**
   * Check in a patient for an appointment.
   */
  async checkIn(id: UUID): Promise<Appointment> {
    const { data } = await api.post<Appointment>(`/appointments/${id}/check-in`);
    return data;
  },

  /**
   * Mark an appointment as no-show.
   */
  async markNoShow(id: UUID): Promise<Appointment> {
    const { data } = await api.post<Appointment>(`/appointments/${id}/no-show`);
    return data;
  },

  /**
   * Get available time slots for a provider on a given date range.
   */
  async getAvailability(params: {
    providerId: UUID;
    startDate: string;
    endDate: string;
    duration?: number;
  }): Promise<AvailabilitySlot[]> {
    const { data } = await api.get<AvailabilitySlot[]>(
      '/appointments/availability',
      { params },
    );
    return data;
  },

  /**
   * Get today's appointments for the current provider.
   */
  async getTodayAppointments(): Promise<Appointment[]> {
    const today = new Date().toISOString().split('T')[0];
    const { data } = await api.get<PaginatedResponse<Appointment>>(
      '/appointments',
      {
        params: { date: today, pageSize: 100 },
      },
    );
    return data.data;
  },

  /**
   * Get appointments for a specific date range (for calendar view).
   */
  async getAppointmentsForRange(
    startDate: string,
    endDate: string,
    providerId?: UUID,
  ): Promise<Appointment[]> {
    const { data } = await api.get<PaginatedResponse<Appointment>>(
      '/appointments',
      {
        params: { startDate, endDate, providerId, pageSize: 200 },
      },
    );
    return data.data;
  },
};
