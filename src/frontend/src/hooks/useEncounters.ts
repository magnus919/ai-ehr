import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query';
import { encounterService } from '@/services/encounters';
import type {
  Encounter,
  EncounterCreateInput,
  EncounterUpdateInput,
  UUID,
} from '@/types';
import type { ICD10Code } from '@/types/api';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/services/api';
import { patientKeys } from './usePatients';

// -----------------------------------------------------------------------------
// Query Keys
// -----------------------------------------------------------------------------

export const encounterKeys = {
  all: ['encounters'] as const,
  lists: () => [...encounterKeys.all, 'list'] as const,
  list: (params?: Record<string, unknown>) =>
    [...encounterKeys.lists(), params] as const,
  details: () => [...encounterKeys.all, 'detail'] as const,
  detail: (id: UUID) => [...encounterKeys.details(), id] as const,
  icd10: (query: string) => ['icd10', 'search', query] as const,
};

// -----------------------------------------------------------------------------
// Queries
// -----------------------------------------------------------------------------

/**
 * Fetch a paginated list of encounters.
 */
export function useEncounters(params?: {
  patientId?: UUID;
  providerId?: UUID;
  status?: string;
  startDate?: string;
  endDate?: string;
  page?: number;
  pageSize?: number;
}) {
  return useQuery({
    queryKey: encounterKeys.list(params as Record<string, unknown>),
    queryFn: () => encounterService.getEncounters(params),
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

/**
 * Fetch a single encounter by ID.
 */
export function useEncounter(id: UUID | undefined) {
  return useQuery({
    queryKey: encounterKeys.detail(id!),
    queryFn: () => encounterService.getEncounter(id!),
    enabled: !!id,
    staleTime: 30_000,
  });
}

/**
 * Search ICD-10 codes.
 */
export function useICD10Search(query: string) {
  return useQuery({
    queryKey: encounterKeys.icd10(query),
    queryFn: () => encounterService.searchICD10(query),
    enabled: query.length >= 2,
    staleTime: 5 * 60_000,
  });
}

// -----------------------------------------------------------------------------
// Mutations
// -----------------------------------------------------------------------------

/**
 * Create a new encounter.
 */
export function useCreateEncounter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: EncounterCreateInput) =>
      encounterService.createEncounter(input),
    onSuccess: (encounter) => {
      queryClient.invalidateQueries({ queryKey: encounterKeys.lists() });
      queryClient.setQueryData(encounterKeys.detail(encounter.id), encounter);
      if (encounter.subject?.reference) {
        const patientId = encounter.subject.reference.split('/').pop();
        if (patientId) {
          queryClient.invalidateQueries({
            queryKey: patientKeys.encounters(patientId),
          });
        }
      }
      toast.success('Encounter created successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

/**
 * Update an existing encounter.
 */
export function useUpdateEncounter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      input,
    }: {
      id: UUID;
      input: EncounterUpdateInput;
    }) => encounterService.updateEncounter(id, input),
    onSuccess: (encounter) => {
      queryClient.invalidateQueries({ queryKey: encounterKeys.lists() });
      queryClient.setQueryData(encounterKeys.detail(encounter.id), encounter);
      toast.success('Encounter updated successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

/**
 * Start an encounter (move to in-progress).
 */
export function useStartEncounter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: UUID) => encounterService.startEncounter(id),
    onSuccess: (encounter) => {
      queryClient.setQueryData(encounterKeys.detail(encounter.id), encounter);
      queryClient.invalidateQueries({ queryKey: encounterKeys.lists() });
      toast.success('Encounter started');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

/**
 * Complete an encounter.
 */
export function useCompleteEncounter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: UUID) => encounterService.completeEncounter(id),
    onSuccess: (encounter) => {
      queryClient.setQueryData(encounterKeys.detail(encounter.id), encounter);
      queryClient.invalidateQueries({ queryKey: encounterKeys.lists() });
      toast.success('Encounter completed');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

/**
 * Cancel an encounter.
 */
export function useCancelEncounter() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, reason }: { id: UUID; reason?: string }) =>
      encounterService.cancelEncounter(id, reason),
    onSuccess: (encounter) => {
      queryClient.setQueryData(encounterKeys.detail(encounter.id), encounter);
      queryClient.invalidateQueries({ queryKey: encounterKeys.lists() });
      toast.success('Encounter cancelled');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}
