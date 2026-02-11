import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { User, AuthTokens } from '@/types';
import { STORAGE_KEYS, SESSION_TIMEOUT_MS, SESSION_WARNING_MS } from '@/utils/constants';

// -----------------------------------------------------------------------------
// Auth Store Types
// -----------------------------------------------------------------------------

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  mfaPending: boolean;
  mfaToken: string | null;
  lastActivity: number;
  sessionWarningVisible: boolean;
}

interface AuthActions {
  setUser: (user: User) => void;
  setTokens: (tokens: AuthTokens) => void;
  login: (user: User, tokens: AuthTokens) => void;
  logout: () => void;
  setLoading: (loading: boolean) => void;
  setMFAPending: (pending: boolean, mfaToken?: string) => void;
  updateLastActivity: () => void;
  setSessionWarning: (visible: boolean) => void;
  checkSessionTimeout: () => boolean;
}

type AuthStore = AuthState & AuthActions;

// -----------------------------------------------------------------------------
// Auth Store
// -----------------------------------------------------------------------------

export const useAuthStore = create<AuthStore>()(
  devtools(
    persist(
      (set, get) => ({
        // State
        user: null,
        accessToken: null,
        refreshToken: null,
        isAuthenticated: false,
        isLoading: false,
        mfaPending: false,
        mfaToken: null,
        lastActivity: Date.now(),
        sessionWarningVisible: false,

        // Actions
        setUser: (user) => set({ user }, false, 'setUser'),

        setTokens: (tokens) =>
          set(
            {
              accessToken: tokens.accessToken,
              refreshToken: tokens.refreshToken,
            },
            false,
            'setTokens',
          ),

        login: (user, tokens) => {
          localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, tokens.accessToken);
          localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, tokens.refreshToken);
          set(
            {
              user,
              accessToken: tokens.accessToken,
              refreshToken: tokens.refreshToken,
              isAuthenticated: true,
              mfaPending: false,
              mfaToken: null,
              lastActivity: Date.now(),
              sessionWarningVisible: false,
            },
            false,
            'login',
          );
        },

        logout: () => {
          localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
          localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
          localStorage.removeItem(STORAGE_KEYS.USER);
          set(
            {
              user: null,
              accessToken: null,
              refreshToken: null,
              isAuthenticated: false,
              mfaPending: false,
              mfaToken: null,
              sessionWarningVisible: false,
            },
            false,
            'logout',
          );
        },

        setLoading: (loading) => set({ isLoading: loading }, false, 'setLoading'),

        setMFAPending: (pending, mfaToken) =>
          set(
            { mfaPending: pending, mfaToken: mfaToken ?? null },
            false,
            'setMFAPending',
          ),

        updateLastActivity: () =>
          set(
            { lastActivity: Date.now(), sessionWarningVisible: false },
            false,
            'updateLastActivity',
          ),

        setSessionWarning: (visible) =>
          set({ sessionWarningVisible: visible }, false, 'setSessionWarning'),

        checkSessionTimeout: () => {
          const { lastActivity, isAuthenticated } = get();
          if (!isAuthenticated) return false;

          const elapsed = Date.now() - lastActivity;

          if (elapsed >= SESSION_TIMEOUT_MS) {
            get().logout();
            return true;
          }

          if (elapsed >= SESSION_TIMEOUT_MS - SESSION_WARNING_MS) {
            set({ sessionWarningVisible: true });
          }

          return false;
        },
      }),
      {
        name: 'omr-auth-storage',
        partialize: (state) => ({
          user: state.user,
          accessToken: state.accessToken,
          refreshToken: state.refreshToken,
          isAuthenticated: state.isAuthenticated,
        }),
      },
    ),
    { name: 'AuthStore' },
  ),
);
