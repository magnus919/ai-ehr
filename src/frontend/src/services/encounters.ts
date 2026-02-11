import api from './api';
import type {
  Encounter,
  EncounterCreateInput,
  EncounterUpdateInput,
  UUID,
} from '@/types';
import type { PaginatedResponse, ICD10Code } from '@/types/api';

// -----------------------------------------------------------------------------
// Encounter API Service
// -----------------------------------------------------------------------------

export const encounterService = {
  /**
   * Get a paginated list of encounters.
   */
  async getEncounters(params?: {
    patientId?: UUID;
    providerId?: UUID;
    status?: string;
    startDate?: string;
    endDate?: string;
    page?: number;
    pageSize?: number;
  }): Promise<PaginatedResponse<Encounter>> {
    const { data } = await api.get<PaginatedResponse<Encounter>>('/encounters', {
      params,
    });
    return data;
  },

  /**
   * Get a single encounter by ID.
   */
  async getEncounter(id: UUID): Promise<Encounter> {
    const { data } = await api.get<Encounter>(`/encounters/${id}`);
    return data;
  },

  /**
   * Create a new encounter.
   */
  async createEncounter(input: EncounterCreateInput): Promise<Encounter> {
    const { data } = await api.post<Encounter>('/encounters', input);
    return data;
  },

  /**
   * Update an existing encounter.
   */
  async updateEncounter(
    id: UUID,
    input: EncounterUpdateInput,
  ): Promise<Encounter> {
    const { data } = await api.put<Encounter>(`/encounters/${id}`, input);
    return data;
  },

  /**
   * Start an encounter (transition to in-progress).
   */
  async startEncounter(id: UUID): Promise<Encounter> {
    const { data } = await api.post<Encounter>(`/encounters/${id}/start`);
    return data;
  },

  /**
   * Complete an encounter (transition to finished).
   */
  async completeEncounter(id: UUID): Promise<Encounter> {
    const { data } = await api.post<Encounter>(`/encounters/${id}/complete`);
    return data;
  },

  /**
   * Cancel an encounter.
   */
  async cancelEncounter(id: UUID, reason?: string): Promise<Encounter> {
    const { data } = await api.post<Encounter>(`/encounters/${id}/cancel`, {
      reason,
    });
    return data;
  },

  /**
   * Search ICD-10 codes for diagnosis entry.
   */
  async searchICD10(query: string): Promise<ICD10Code[]> {
    const { data } = await api.get<ICD10Code[]>('/reference/icd10/search', {
      params: { q: query },
    });
    return data;
  },

  /**
   * Add a diagnosis to an encounter.
   */
  async addDiagnosis(
    encounterId: UUID,
    diagnosis: { code: string; display: string; rank?: number },
  ): Promise<Encounter> {
    const { data } = await api.post<Encounter>(
      `/encounters/${encounterId}/diagnoses`,
      diagnosis,
    );
    return data;
  },

  /**
   * Remove a diagnosis from an encounter.
   */
  async removeDiagnosis(
    encounterId: UUID,
    conditionId: UUID,
  ): Promise<void> {
    await api.delete(`/encounters/${encounterId}/diagnoses/${conditionId}`);
  },
};
