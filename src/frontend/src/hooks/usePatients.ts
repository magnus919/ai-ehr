import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query';
import { patientService } from '@/services/patients';
import type {
  PatientCreateInput,
  PatientUpdateInput,
  PatientSearchParams,
  UUID,
} from '@/types';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/services/api';

// -----------------------------------------------------------------------------
// Query Keys
// -----------------------------------------------------------------------------

export const patientKeys = {
  all: ['patients'] as const,
  lists: () => [...patientKeys.all, 'list'] as const,
  list: (params?: PatientSearchParams) =>
    [...patientKeys.lists(), params] as const,
  details: () => [...patientKeys.all, 'detail'] as const,
  detail: (id: UUID) => [...patientKeys.details(), id] as const,
  search: (query: string) => [...patientKeys.all, 'search', query] as const,
  encounters: (id: UUID) => [...patientKeys.detail(id), 'encounters'] as const,
  medications: (id: UUID) => [...patientKeys.detail(id), 'medications'] as const,
  conditions: (id: UUID) => [...patientKeys.detail(id), 'conditions'] as const,
  observations: (id: UUID) =>
    [...patientKeys.detail(id), 'observations'] as const,
  orders: (id: UUID) => [...patientKeys.detail(id), 'orders'] as const,
};

// -----------------------------------------------------------------------------
// Queries
// -----------------------------------------------------------------------------

/**
 * Fetch a paginated list of patients.
 */
export function usePatients(params?: PatientSearchParams) {
  return useQuery({
    queryKey: patientKeys.list(params),
    queryFn: () => patientService.getPatients(params),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

/**
 * Fetch a single patient by ID.
 */
export function usePatient(id: UUID | undefined) {
  return useQuery({
    queryKey: patientKeys.detail(id!),
    queryFn: () => patientService.getPatient(id!),
    enabled: !!id,
    staleTime: 60_000,
  });
}

/**
 * Search patients (for autocomplete / patient search).
 */
export function usePatientSearch(query: string) {
  return useQuery({
    queryKey: patientKeys.search(query),
    queryFn: () => patientService.searchPatients(query),
    enabled: query.length >= 2,
    staleTime: 10_000,
  });
}

/**
 * Fetch encounters for a patient.
 */
export function usePatientEncounters(
  patientId: UUID | undefined,
  params?: { page?: number; pageSize?: number },
) {
  return useQuery({
    queryKey: [...patientKeys.encounters(patientId!), params],
    queryFn: () => patientService.getPatientEncounters(patientId!, params),
    enabled: !!patientId,
    staleTime: 30_000,
  });
}

/**
 * Fetch medications for a patient.
 */
export function usePatientMedications(
  patientId: UUID | undefined,
  params?: { status?: string },
) {
  return useQuery({
    queryKey: [...patientKeys.medications(patientId!), params],
    queryFn: () => patientService.getPatientMedications(patientId!, params),
    enabled: !!patientId,
    staleTime: 60_000,
  });
}

/**
 * Fetch conditions / problem list for a patient.
 */
export function usePatientConditions(patientId: UUID | undefined) {
  return useQuery({
    queryKey: patientKeys.conditions(patientId!),
    queryFn: () => patientService.getPatientConditions(patientId!),
    enabled: !!patientId,
    staleTime: 60_000,
  });
}

/**
 * Fetch observations (labs, vitals) for a patient.
 */
export function usePatientObservations(
  patientId: UUID | undefined,
  params?: { category?: string; page?: number; pageSize?: number },
) {
  return useQuery({
    queryKey: [...patientKeys.observations(patientId!), params],
    queryFn: () => patientService.getPatientObservations(patientId!, params),
    enabled: !!patientId,
    staleTime: 30_000,
  });
}

// -----------------------------------------------------------------------------
// Mutations
// -----------------------------------------------------------------------------

/**
 * Create a new patient.
 */
export function useCreatePatient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: PatientCreateInput) =>
      patientService.createPatient(input),
    onSuccess: (patient) => {
      queryClient.invalidateQueries({ queryKey: patientKeys.lists() });
      queryClient.setQueryData(patientKeys.detail(patient.id), patient);
      toast.success('Patient created successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

/**
 * Update an existing patient.
 */
export function useUpdatePatient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: UUID; input: PatientUpdateInput }) =>
      patientService.updatePatient(id, input),
    onSuccess: (patient) => {
      queryClient.invalidateQueries({ queryKey: patientKeys.lists() });
      queryClient.setQueryData(patientKeys.detail(patient.id), patient);
      toast.success('Patient updated successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

/**
 * Deactivate a patient.
 */
export function useDeactivatePatient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: UUID) => patientService.deactivatePatient(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: patientKeys.lists() });
      queryClient.invalidateQueries({ queryKey: patientKeys.detail(id) });
      toast.success('Patient deactivated');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}
