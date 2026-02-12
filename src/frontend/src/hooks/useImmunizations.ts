import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query';
import {
  immunizationsApi,
  type ImmunizationCreate,
} from '@/services/immunizations';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/services/api';

// Query Keys
export const immunizationKeys = {
  all: ['immunizations'] as const,
  lists: () => [...immunizationKeys.all, 'list'] as const,
  list: (params?: Record<string, string>) =>
    [...immunizationKeys.lists(), params] as const,
  details: () => [...immunizationKeys.all, 'detail'] as const,
  detail: (id: string) => [...immunizationKeys.details(), id] as const,
};

// Queries
export function useImmunizations(params?: Record<string, string>) {
  return useQuery({
    queryKey: immunizationKeys.list(params),
    queryFn: async () => {
      const { data } = await immunizationsApi.list(params);
      return data;
    },
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useImmunization(id: string | undefined) {
  return useQuery({
    queryKey: immunizationKeys.detail(id!),
    queryFn: async () => {
      const { data } = await immunizationsApi.get(id!);
      return data;
    },
    enabled: !!id,
    staleTime: 60_000,
  });
}

// Mutations
export function useCreateImmunization() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ImmunizationCreate) =>
      immunizationsApi.create(input).then(res => res.data),
    onSuccess: (immunization) => {
      queryClient.invalidateQueries({ queryKey: immunizationKeys.lists() });
      queryClient.setQueryData(immunizationKeys.detail(immunization.id), immunization);
      toast.success('Immunization created successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

export function useUpdateImmunization() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: Record<string, unknown> }) =>
      immunizationsApi.update(id, input).then(res => res.data),
    onSuccess: (immunization) => {
      queryClient.invalidateQueries({ queryKey: immunizationKeys.lists() });
      queryClient.setQueryData(immunizationKeys.detail(immunization.id), immunization);
      toast.success('Immunization updated successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}
