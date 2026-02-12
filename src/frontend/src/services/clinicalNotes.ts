import api from './api';

export interface ClinicalNote {
  id: string;
  tenant_id: string;
  patient_id: string;
  encounter_id?: string;
  note_type: string;
  status: string;
  author_id: string;
  is_psychotherapy_note: boolean;
  is_42cfr_part2: boolean;
  signed_at?: string;
  signed_by?: string;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface ClinicalNoteCreate {
  patient_id: string;
  encounter_id?: string;
  note_type: string;
  content: string;
  is_psychotherapy_note?: boolean;
  is_42cfr_part2?: boolean;
}

export interface ClinicalNoteUpdate {
  content?: string;
  status?: string;
}

export const clinicalNotesApi = {
  list: (params?: Record<string, string>) =>
    api.get<ClinicalNote[]>('/clinical-notes', { params }),
  get: (id: string) => api.get<ClinicalNote>(`/clinical-notes/${id}`),
  create: (data: ClinicalNoteCreate) =>
    api.post<ClinicalNote>('/clinical-notes', data),
  update: (id: string, data: ClinicalNoteUpdate) =>
    api.put<ClinicalNote>(`/clinical-notes/${id}`, data),
  sign: (id: string) =>
    api.post<ClinicalNote>(`/clinical-notes/${id}/sign`),
};
