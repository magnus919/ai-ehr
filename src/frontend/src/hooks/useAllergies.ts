import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query';
import {
  allergiesApi,
  type AllergyIntolerance,
  type AllergyCreate,
  type AllergyUpdate,
} from '@/services/allergies';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/services/api';

// Query Keys
export const allergyKeys = {
  all: ['allergies'] as const,
  lists: () => [...allergyKeys.all, 'list'] as const,
  list: (params?: Record<string, string>) =>
    [...allergyKeys.lists(), params] as const,
  details: () => [...allergyKeys.all, 'detail'] as const,
  detail: (id: string) => [...allergyKeys.details(), id] as const,
};

// Queries
export function useAllergies(params?: Record<string, string>) {
  return useQuery({
    queryKey: allergyKeys.list(params),
    queryFn: async () => {
      const { data } = await allergiesApi.list(params);
      return data;
    },
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useAllergy(id: string | undefined) {
  return useQuery({
    queryKey: allergyKeys.detail(id!),
    queryFn: async () => {
      const { data } = await allergiesApi.get(id!);
      return data;
    },
    enabled: !!id,
    staleTime: 60_000,
  });
}

// Mutations
export function useCreateAllergy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: AllergyCreate) =>
      allergiesApi.create(input).then(res => res.data),
    onSuccess: (allergy) => {
      queryClient.invalidateQueries({ queryKey: allergyKeys.lists() });
      queryClient.setQueryData(allergyKeys.detail(allergy.id), allergy);
      toast.success('Allergy created successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

export function useUpdateAllergy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: AllergyUpdate }) =>
      allergiesApi.update(id, input).then(res => res.data),
    onSuccess: (allergy) => {
      queryClient.invalidateQueries({ queryKey: allergyKeys.lists() });
      queryClient.setQueryData(allergyKeys.detail(allergy.id), allergy);
      toast.success('Allergy updated successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}

export function useDeactivateAllergy() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => allergiesApi.deactivate(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: allergyKeys.lists() });
      queryClient.invalidateQueries({ queryKey: allergyKeys.detail(id) });
      toast.success('Allergy deactivated');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}
