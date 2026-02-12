import api from './api';

export interface Consent {
  id: string;
  tenant_id: string;
  patient_id: string;
  status: string;
  scope: string;
  category: string;
  provision_type: string;
  period_start?: string;
  period_end?: string;
  policy_rule?: string;
  note?: string;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface ConsentCreate {
  patient_id: string;
  scope: string;
  category: string;
  provision_type?: string;
  period_start?: string;
  period_end?: string;
  policy_rule?: string;
  note?: string;
}

export const consentsApi = {
  list: (params?: Record<string, string>) =>
    api.get<Consent[]>('/consents', { params }),
  get: (id: string) => api.get<Consent>(`/consents/${id}`),
  create: (data: ConsentCreate) => api.post<Consent>('/consents', data),
  update: (id: string, data: Record<string, unknown>) =>
    api.put<Consent>(`/consents/${id}`, data),
  withdraw: (id: string) => api.post<Consent>(`/consents/${id}/withdraw`),
};
