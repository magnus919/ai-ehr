import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Link } from 'react-router-dom';
import { EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';
import { useAuth } from '@/hooks/useAuth';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { APP_NAME } from '@/utils/constants';

// -----------------------------------------------------------------------------
// Validation Schemas
// -----------------------------------------------------------------------------

const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters'),
});

const mfaSchema = z.object({
  mfaCode: z
    .string()
    .min(6, 'Please enter the 6-digit code')
    .max(6, 'Please enter the 6-digit code')
    .regex(/^\d{6}$/, 'Code must be 6 digits'),
});

type LoginFormData = z.infer<typeof loginSchema>;
type MFAFormData = z.infer<typeof mfaSchema>;

// -----------------------------------------------------------------------------
// LoginForm Component
// -----------------------------------------------------------------------------

export function LoginForm() {
  const { login, verifyMFA, isLoading, mfaPending } = useAuth();
  const [showPassword, setShowPassword] = useState(false);

  // Login form
  const loginForm = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  // MFA form
  const mfaForm = useForm<MFAFormData>({
    resolver: zodResolver(mfaSchema),
    defaultValues: { mfaCode: '' },
  });

  const handleLogin = async (data: LoginFormData) => {
    try {
      await login({ email: data.email, password: data.password });
    } catch {
      // Error is handled in the hook via toast
    }
  };

  const handleMFA = async (data: MFAFormData) => {
    try {
      await verifyMFA(data.mfaCode);
    } catch {
      mfaForm.setError('mfaCode', { message: 'Invalid code. Please try again.' });
    }
  };

  // ---------------------------------------------------------------------------
  // MFA Step
  // ---------------------------------------------------------------------------

  if (mfaPending) {
    return (
      <div className="w-full max-w-sm">
        <div className="text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary-600 text-white">
            <svg
              className="h-7 w-7"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 4.5v15m7.5-7.5h-15"
              />
            </svg>
          </div>
          <h1 className="mt-4 text-2xl font-bold text-gray-900 dark:text-white">
            Two-Factor Authentication
          </h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Enter the 6-digit code from your authenticator app.
          </p>
        </div>

        <form onSubmit={mfaForm.handleSubmit(handleMFA)} className="mt-8 space-y-6">
          <div>
            <label
              htmlFor="mfaCode"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Verification Code
            </label>
            <input
              id="mfaCode"
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              autoFocus
              {...mfaForm.register('mfaCode')}
              className="input-base mt-1 text-center text-2xl tracking-[0.5em]"
              placeholder="000000"
              aria-describedby={
                mfaForm.formState.errors.mfaCode ? 'mfa-error' : undefined
              }
              aria-invalid={!!mfaForm.formState.errors.mfaCode}
            />
            {mfaForm.formState.errors.mfaCode && (
              <p id="mfa-error" className="mt-1 text-sm text-red-600" role="alert">
                {mfaForm.formState.errors.mfaCode.message}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn-primary w-full"
          >
            {isLoading ? (
              <LoadingSpinner size="sm" label="Verifying..." />
            ) : (
              'Verify'
            )}
          </button>
        </form>
      </div>
    );
  }

  // ---------------------------------------------------------------------------
  // Login Step
  // ---------------------------------------------------------------------------

  return (
    <div className="w-full max-w-sm">
      {/* Logo and Title */}
      <div className="text-center">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary-600 text-white">
          <svg
            className="h-7 w-7"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={2}
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 4.5v15m7.5-7.5h-15"
            />
          </svg>
        </div>
        <h1 className="mt-4 text-2xl font-bold text-gray-900 dark:text-white">
          Sign in to {APP_NAME}
        </h1>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          Enter your credentials to access the system
        </p>
      </div>

      {/* Form */}
      <form
        onSubmit={loginForm.handleSubmit(handleLogin)}
        className="mt-8 space-y-5"
        noValidate
      >
        {/* Email Field */}
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Email Address
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            autoFocus
            {...loginForm.register('email')}
            className="input-base mt-1"
            placeholder="you@clinic.com"
            aria-describedby={
              loginForm.formState.errors.email ? 'email-error' : undefined
            }
            aria-invalid={!!loginForm.formState.errors.email}
          />
          {loginForm.formState.errors.email && (
            <p id="email-error" className="mt-1 text-sm text-red-600" role="alert">
              {loginForm.formState.errors.email.message}
            </p>
          )}
        </div>

        {/* Password Field */}
        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300"
          >
            Password
          </label>
          <div className="relative mt-1">
            <input
              id="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              {...loginForm.register('password')}
              className="input-base pr-10"
              placeholder="Enter your password"
              aria-describedby={
                loginForm.formState.errors.password
                  ? 'password-error'
                  : undefined
              }
              aria-invalid={!!loginForm.formState.errors.password}
            />
            <button
              type="button"
              className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
              onClick={() => setShowPassword(!showPassword)}
              aria-label={showPassword ? 'Hide password' : 'Show password'}
            >
              {showPassword ? (
                <EyeSlashIcon className="h-4 w-4" />
              ) : (
                <EyeIcon className="h-4 w-4" />
              )}
            </button>
          </div>
          {loginForm.formState.errors.password && (
            <p
              id="password-error"
              className="mt-1 text-sm text-red-600"
              role="alert"
            >
              {loginForm.formState.errors.password.message}
            </p>
          )}
        </div>

        {/* Forgot Password Link */}
        <div className="flex items-center justify-end">
          <Link
            to="/forgot-password"
            className="text-sm font-medium text-primary-600 hover:text-primary-500 dark:text-primary-400"
          >
            Forgot your password?
          </Link>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isLoading}
          className="btn-primary w-full"
        >
          {isLoading ? (
            <LoadingSpinner size="sm" label="Signing in..." />
          ) : (
            'Sign In'
          )}
        </button>
      </form>

      {/* Footer */}
      <p className="mt-6 text-center text-xs text-gray-500 dark:text-gray-400">
        Protected health information. Authorized users only.
        <br />
        All access is monitored and logged.
      </p>
    </div>
  );
}
