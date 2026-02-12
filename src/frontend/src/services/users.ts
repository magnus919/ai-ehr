import api from './api';

export interface User {
  id: string;
  tenant_id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  npi?: string;
  is_active: boolean;
  mfa_enabled: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export interface UserUpdate {
  first_name?: string;
  last_name?: string;
  role?: string;
  npi?: string;
  is_active?: boolean;
}

export const usersApi = {
  list: (params?: Record<string, string>) =>
    api.get<User[]>('/users', { params }),
  get: (id: string) => api.get<User>(`/users/${id}`),
  update: (id: string, data: UserUpdate) =>
    api.put<User>(`/users/${id}`, data),
};
