import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query';
import {
  clinicalNotesApi,
  type ClinicalNoteCreate,
  type ClinicalNoteUpdate,
} from '@/services/clinicalNotes';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/services/api';

// Query Keys
export const clinicalNoteKeys = {
  all: ['clinicalNotes'] as const,
  lists: () => [...clinicalNoteKeys.all, 'list'] as const,
  list: (params?: Record<string, string>) =>
    [...clinicalNoteKeys.lists(), params] as const,
  details: () => [...clinicalNoteKeys.all, 'detail'] as const,
  detail: (id: string) => [...clinicalNoteKeys.details(), id] as const,
};

// Queries
export function useClinicalNotes(params?: Record<string, string>) {
  return useQuery({
    queryKey: clinicalNoteKeys.list(params),
    queryFn: async () => {
      const { data } = await clinicalNotesApi.list(params);
      return data;
    },
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useClinicalNote(id: string | undefined) {
  return useQuery({
    queryKey: clinicalNoteKeys.detail(id!),
    queryFn: async () => {
      const { data } = await clinicalNotesApi.get(id!);
      return data;
    },
    enabled: !!id,
    staleTime: 60_000,
  });
}

// Mutations
export function useCreateClinicalNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ClinicalNoteCreate) =>
      clinicalNotesApi.create(input).then(res => res.data),
    onSuccess: (note) => {
      queryClient.invalidateQueries({ queryKey: clinicalNoteKeys.lists() });
      queryClient.setQueryData(clinicalNoteKeys.detail(note.id), note);
      toast.success('Clinical note created successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

export function useUpdateClinicalNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: ClinicalNoteUpdate }) =>
      clinicalNotesApi.update(id, input).then(res => res.data),
    onSuccess: (note) => {
      queryClient.invalidateQueries({ queryKey: clinicalNoteKeys.lists() });
      queryClient.setQueryData(clinicalNoteKeys.detail(note.id), note);
      toast.success('Clinical note updated successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

export function useSignClinicalNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => clinicalNotesApi.sign(id).then(res => res.data),
    onSuccess: (note) => {
      queryClient.invalidateQueries({ queryKey: clinicalNoteKeys.lists() });
      queryClient.setQueryData(clinicalNoteKeys.detail(note.id), note);
      toast.success('Clinical note signed successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}
