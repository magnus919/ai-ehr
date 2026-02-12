import {
  useQuery,
  useMutation,
  useQueryClient,
  keepPreviousData,
} from '@tanstack/react-query';
import { usersApi, type User, type UserUpdate } from '@/services/users';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/services/api';

// Query Keys
export const userKeys = {
  all: ['users'] as const,
  lists: () => [...userKeys.all, 'list'] as const,
  list: (params?: Record<string, string>) =>
    [...userKeys.lists(), params] as const,
  details: () => [...userKeys.all, 'detail'] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
};

// Queries
export function useUsers(params?: Record<string, string>) {
  return useQuery({
    queryKey: userKeys.list(params),
    queryFn: async () => {
      const { data } = await usersApi.list(params);
      return data;
    },
    placeholderData: keepPreviousData,
    staleTime: 30_000,
  });
}

export function useUser(id: string | undefined) {
  return useQuery({
    queryKey: userKeys.detail(id!),
    queryFn: async () => {
      const { data } = await usersApi.get(id!);
      return data;
    },
    enabled: !!id,
    staleTime: 60_000,
  });
}

// Mutations
export function useUpdateUser() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, input }: { id: string; input: UserUpdate }) =>
      usersApi.update(id, input).then(res => res.data),
    onSuccess: (user) => {
      queryClient.invalidateQueries({ queryKey: userKeys.lists() });
      queryClient.setQueryData(userKeys.detail(user.id), user);
      toast.success('User updated successfully');
    },
    onError: (error) => {
      toast.error(getErrorMessage(error));
    },
  });
}
