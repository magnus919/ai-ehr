import api from './api';
import type {
  Patient,
  PatientCreateInput,
  PatientUpdateInput,
  PatientSearchParams,
  UUID,
} from '@/types';
import type { PaginatedResponse, SearchResult } from '@/types/api';

// -----------------------------------------------------------------------------
// Patient API Service
// -----------------------------------------------------------------------------

export const patientService = {
  /**
   * Get a paginated list of patients.
   */
  async getPatients(
    params?: PatientSearchParams,
  ): Promise<PaginatedResponse<Patient>> {
    const { data } = await api.get<PaginatedResponse<Patient>>('/patients', {
      params,
    });
    return data;
  },

  /**
   * Get a single patient by ID.
   */
  async getPatient(id: UUID): Promise<Patient> {
    const { data } = await api.get<Patient>(`/patients/${id}`);
    return data;
  },

  /**
   * Create a new patient.
   */
  async createPatient(input: PatientCreateInput): Promise<Patient> {
    const { data } = await api.post<Patient>('/patients', input);
    return data;
  },

  /**
   * Update an existing patient.
   */
  async updatePatient(id: UUID, input: PatientUpdateInput): Promise<Patient> {
    const { data } = await api.put<Patient>(`/patients/${id}`, input);
    return data;
  },

  /**
   * Deactivate a patient record.
   */
  async deactivatePatient(id: UUID): Promise<void> {
    await api.patch(`/patients/${id}/deactivate`);
  },

  /**
   * Search patients by name, MRN, or DOB (for autocomplete).
   */
  async searchPatients(query: string): Promise<SearchResult<Patient>> {
    const { data } = await api.get<SearchResult<Patient>>('/patients/search', {
      params: { q: query },
    });
    return data;
  },

  /**
   * Get a patient's encounter history.
   */
  async getPatientEncounters(
    patientId: UUID,
    params?: { page?: number; pageSize?: number },
  ): Promise<PaginatedResponse<import('@/types').Encounter>> {
    const { data } = await api.get(`/patients/${patientId}/encounters`, {
      params,
    });
    return data;
  },

  /**
   * Get a patient's medication list.
   */
  async getPatientMedications(
    patientId: UUID,
    params?: { status?: string },
  ): Promise<import('@/types').MedicationRequest[]> {
    const { data } = await api.get(`/patients/${patientId}/medications`, {
      params,
    });
    return data;
  },

  /**
   * Get a patient's conditions/problem list.
   */
  async getPatientConditions(
    patientId: UUID,
  ): Promise<import('@/types').Condition[]> {
    const { data } = await api.get(`/patients/${patientId}/conditions`);
    return data;
  },

  /**
   * Get a patient's observations (lab results, vitals).
   */
  async getPatientObservations(
    patientId: UUID,
    params?: { category?: string; page?: number; pageSize?: number },
  ): Promise<PaginatedResponse<import('@/types').Observation>> {
    const { data } = await api.get(`/patients/${patientId}/observations`, {
      params,
    });
    return data;
  },

  /**
   * Get a patient's orders.
   */
  async getPatientOrders(
    patientId: UUID,
    params?: { type?: string; status?: string },
  ): Promise<import('@/types').Order[]> {
    const { data } = await api.get(`/patients/${patientId}/orders`, {
      params,
    });
    return data;
  },
};
