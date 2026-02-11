import { useCallback, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { authService, isMFAChallenge } from '@/services/auth';
import type { LoginCredentials } from '@/types';
import toast from 'react-hot-toast';
import { getErrorMessage } from '@/services/api';
import { SESSION_TIMEOUT_MS } from '@/utils/constants';

// -----------------------------------------------------------------------------
// useAuth Hook
// -----------------------------------------------------------------------------

export function useAuth() {
  const {
    user,
    isAuthenticated,
    isLoading,
    mfaPending,
    mfaToken,
    sessionWarningVisible,
    login: storeLogin,
    logout: storeLogout,
    setLoading,
    setMFAPending,
    updateLastActivity,
    setSessionWarning,
    checkSessionTimeout,
  } = useAuthStore();

  const navigate = useNavigate();
  const sessionTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ---------------------------------------------------------------------------
  // Session timeout monitoring
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!isAuthenticated) {
      if (sessionTimerRef.current) {
        clearInterval(sessionTimerRef.current);
        sessionTimerRef.current = null;
      }
      return;
    }

    // Check session every 30 seconds
    sessionTimerRef.current = setInterval(() => {
      const timedOut = checkSessionTimeout();
      if (timedOut) {
        toast.error('Session expired. Please log in again.');
        navigate('/login');
      }
    }, 30_000);

    return () => {
      if (sessionTimerRef.current) {
        clearInterval(sessionTimerRef.current);
      }
    };
  }, [isAuthenticated, checkSessionTimeout, navigate]);

  // ---------------------------------------------------------------------------
  // Activity tracking
  // ---------------------------------------------------------------------------

  useEffect(() => {
    if (!isAuthenticated) return;

    const events = ['mousedown', 'keydown', 'scroll', 'touchstart'];
    const handleActivity = () => updateLastActivity();

    events.forEach((event) => {
      window.addEventListener(event, handleActivity, { passive: true });
    });

    return () => {
      events.forEach((event) => {
        window.removeEventListener(event, handleActivity);
      });
    };
  }, [isAuthenticated, updateLastActivity]);

  // ---------------------------------------------------------------------------
  // Login
  // ---------------------------------------------------------------------------

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      setLoading(true);
      try {
        const response = await authService.login(credentials);

        if (isMFAChallenge(response)) {
          setMFAPending(true, response.mfaToken);
          return { mfaRequired: true as const };
        }

        storeLogin(response.user, response.tokens);
        navigate('/dashboard');
        toast.success(`Welcome back, ${response.user.firstName}!`);
        return { mfaRequired: false as const };
      } catch (error) {
        toast.error(getErrorMessage(error));
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [setLoading, setMFAPending, storeLogin, navigate],
  );

  // ---------------------------------------------------------------------------
  // MFA Verification
  // ---------------------------------------------------------------------------

  const verifyMFA = useCallback(
    async (code: string) => {
      if (!mfaToken) {
        toast.error('MFA session expired. Please login again.');
        return;
      }

      setLoading(true);
      try {
        const response = await authService.verifyMFA(mfaToken, code);
        storeLogin(response.user, response.tokens);
        navigate('/dashboard');
        toast.success(`Welcome back, ${response.user.firstName}!`);
      } catch (error) {
        toast.error(getErrorMessage(error));
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [mfaToken, setLoading, storeLogin, navigate],
  );

  // ---------------------------------------------------------------------------
  // Logout
  // ---------------------------------------------------------------------------

  const logout = useCallback(async () => {
    try {
      await authService.logout();
    } finally {
      storeLogout();
      navigate('/login');
      toast.success('Logged out successfully');
    }
  }, [storeLogout, navigate]);

  // ---------------------------------------------------------------------------
  // Extend Session
  // ---------------------------------------------------------------------------

  const extendSession = useCallback(() => {
    updateLastActivity();
    setSessionWarning(false);
    toast.success('Session extended');
  }, [updateLastActivity, setSessionWarning]);

  return {
    user,
    isAuthenticated,
    isLoading,
    mfaPending,
    sessionWarningVisible,
    login,
    verifyMFA,
    logout,
    extendSession,
  };
}
