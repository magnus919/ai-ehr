import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query';
import { observationsApi, type ObservationCreate } from '@/services/observations';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/services/api';

// Query Keys
export const observationKeys = {
  all: ['observations'] as const,
  lists: () => [...observationKeys.all, 'list'] as const,
  list: (params?: Record<string, string>) =>
    [...observationKeys.lists(), params] as const,
  details: () => [...observationKeys.all, 'detail'] as const,
  detail: (id: string) => [...observationKeys.details(), id] as const,
};

// Queries
export function useObservations(params?: Record<string, string>) {
  return useQuery({
    queryKey: observationKeys.list(params),
    queryFn: async () => {
      const { data } = await observationsApi.list(params);
      return data;
    },
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useObservation(id: string | undefined) {
  return useQuery({
    queryKey: observationKeys.detail(id!),
    queryFn: async () => {
      const { data } = await observationsApi.get(id!);
      return data;
    },
    enabled: !!id,
    staleTime: 60_000,
  });
}

// Mutations
export function useCreateObservation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ObservationCreate) =>
      observationsApi.create(input).then(res => res.data),
    onSuccess: (observation) => {
      queryClient.invalidateQueries({ queryKey: observationKeys.lists() });
      queryClient.setQueryData(observationKeys.detail(observation.id), observation);
      toast.success('Observation created successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}
