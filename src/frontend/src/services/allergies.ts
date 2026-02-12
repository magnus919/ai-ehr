import api from './api';

export interface AllergyIntolerance {
  id: string;
  tenant_id: string;
  patient_id: string;
  clinical_status: string;
  verification_status: string;
  type: string;
  category?: string[];
  criticality?: string;
  code_system: string;
  code: string;
  code_display: string;
  onset_datetime?: string;
  recorded_date: string;
  note?: string;
  reaction?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface AllergyCreate {
  patient_id: string;
  clinical_status?: string;
  verification_status?: string;
  type?: string;
  category?: string[];
  criticality?: string;
  code_system?: string;
  code: string;
  code_display: string;
  onset_datetime?: string;
  note?: string;
  reaction?: Record<string, unknown>;
}

export interface AllergyUpdate {
  clinical_status?: string;
  verification_status?: string;
  criticality?: string;
  note?: string;
  reaction?: Record<string, unknown>;
}

export const allergiesApi = {
  list: (params?: Record<string, string>) =>
    api.get<AllergyIntolerance[]>('/allergies', { params }),
  get: (id: string) => api.get<AllergyIntolerance>(`/allergies/${id}`),
  create: (data: AllergyCreate) => api.post<AllergyIntolerance>('/allergies', data),
  update: (id: string, data: AllergyUpdate) =>
    api.put<AllergyIntolerance>(`/allergies/${id}`, data),
  deactivate: (id: string) => api.delete(`/allergies/${id}`),
};
