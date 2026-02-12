import api from './api';

export interface Observation {
  id: string;
  tenant_id: string;
  patient_id: string;
  encounter_id?: string;
  code: string;
  code_system: string;
  display: string;
  value_type: string;
  value_string?: string;
  value_numeric?: number;
  unit?: string;
  effective_date: string;
  status: string;
  performer_id?: string;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface ObservationCreate {
  patient_id: string;
  encounter_id?: string;
  code: string;
  code_system?: string;
  display: string;
  value_type?: string;
  value_string?: string;
  value_numeric?: number;
  unit?: string;
  effective_date: string;
  status?: string;
  performer_id?: string;
}

export const observationsApi = {
  list: (params?: Record<string, string>) =>
    api.get<Observation[]>('/observations', { params }),
  get: (id: string) => api.get<Observation>(`/observations/${id}`),
  create: (data: ObservationCreate) => api.post<Observation>('/observations', data),
};
