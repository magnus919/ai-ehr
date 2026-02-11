import api from './api';
import type { LoginCredentials, AuthTokens, User, MFASetupResponse } from '@/types';
import type { AuthResponse, MFAChallengeResponse, TokenRefreshResponse } from '@/types/api';

// -----------------------------------------------------------------------------
// Auth Service
// -----------------------------------------------------------------------------

export const authService = {
  /**
   * Login with email and password. Returns user and tokens, or an MFA challenge.
   */
  async login(
    credentials: LoginCredentials,
  ): Promise<AuthResponse | MFAChallengeResponse> {
    const { data } = await api.post<AuthResponse | MFAChallengeResponse>(
      '/auth/login',
      credentials,
    );
    return data;
  },

  /**
   * Complete MFA verification during login.
   */
  async verifyMFA(mfaToken: string, code: string): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>('/auth/mfa/verify', {
      mfaToken,
      code,
    });
    return data;
  },

  /**
   * Register a new user account.
   */
  async register(payload: {
    email: string;
    password: string;
    firstName: string;
    lastName: string;
    role?: string;
  }): Promise<AuthResponse> {
    const { data } = await api.post<AuthResponse>('/auth/register', payload);
    return data;
  },

  /**
   * Logout and invalidate the current session.
   */
  async logout(): Promise<void> {
    try {
      await api.post('/auth/logout');
    } catch {
      // Ignore logout errors - we clear local state regardless
    }
  },

  /**
   * Refresh the access token.
   */
  async refreshToken(refreshToken: string): Promise<TokenRefreshResponse> {
    const { data } = await api.post<TokenRefreshResponse>('/auth/refresh', {
      refreshToken,
    });
    return data;
  },

  /**
   * Get the currently authenticated user's profile.
   */
  async getCurrentUser(): Promise<User> {
    const { data } = await api.get<User>('/auth/me');
    return data;
  },

  /**
   * Update the current user's password.
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await api.post('/auth/change-password', {
      currentPassword,
      newPassword,
    });
  },

  /**
   * Request a password reset email.
   */
  async requestPasswordReset(email: string): Promise<void> {
    await api.post('/auth/forgot-password', { email });
  },

  /**
   * Reset password with token from email.
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    await api.post('/auth/reset-password', { token, newPassword });
  },

  /**
   * Begin MFA setup - returns QR code and backup codes.
   */
  async setupMFA(): Promise<MFASetupResponse> {
    const { data } = await api.post<MFASetupResponse>('/auth/mfa/setup');
    return data;
  },

  /**
   * Enable MFA after verifying initial TOTP code.
   */
  async enableMFA(code: string): Promise<void> {
    await api.post('/auth/mfa/enable', { code });
  },

  /**
   * Disable MFA for the current user.
   */
  async disableMFA(password: string): Promise<void> {
    await api.post('/auth/mfa/disable', { password });
  },

  /**
   * Validate the current access token.
   */
  async validateToken(): Promise<boolean> {
    try {
      await api.get('/auth/validate');
      return true;
    } catch {
      return false;
    }
  },
};

// -----------------------------------------------------------------------------
// Helper: Check if response is an MFA challenge
// -----------------------------------------------------------------------------

export function isMFAChallenge(
  response: AuthResponse | MFAChallengeResponse,
): response is MFAChallengeResponse {
  return 'mfaRequired' in response && response.mfaRequired === true;
}

// -----------------------------------------------------------------------------
// Helper: Store auth tokens in localStorage
// -----------------------------------------------------------------------------

export function storeTokens(tokens: AuthTokens): void {
  localStorage.setItem('omr_access_token', tokens.accessToken);
  localStorage.setItem('omr_refresh_token', tokens.refreshToken);
}

export function clearTokens(): void {
  localStorage.removeItem('omr_access_token');
  localStorage.removeItem('omr_refresh_token');
  localStorage.removeItem('omr_user');
}
