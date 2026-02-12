import api from './api';

export interface Immunization {
  id: string;
  tenant_id: string;
  patient_id: string;
  encounter_id?: string;
  status: string;
  vaccine_code: string;
  vaccine_code_system: string;
  vaccine_display: string;
  occurrence_datetime: string;
  lot_number?: string;
  site_code?: string;
  route_code?: string;
  dose_quantity?: number;
  performer_id?: string;
  note?: string;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface ImmunizationCreate {
  patient_id: string;
  encounter_id?: string;
  status?: string;
  vaccine_code: string;
  vaccine_code_system?: string;
  vaccine_display: string;
  occurrence_datetime: string;
  lot_number?: string;
  site_code?: string;
  route_code?: string;
  dose_quantity?: number;
  performer_id?: string;
  note?: string;
}

export const immunizationsApi = {
  list: (params?: Record<string, string>) =>
    api.get<Immunization[]>('/immunizations', { params }),
  get: (id: string) => api.get<Immunization>(`/immunizations/${id}`),
  create: (data: ImmunizationCreate) =>
    api.post<Immunization>('/immunizations', data),
  update: (id: string, data: Record<string, unknown>) =>
    api.put<Immunization>(`/immunizations/${id}`, data),
};
