import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import axios, { AxiosError } from 'axios';

// ---------------------------------------------------------------------------
// Validation Schema
// ---------------------------------------------------------------------------

const loginSchema = z.object({
  email: z.string().min(1, 'Email is required').email('Please enter a valid email'),
  password: z.string().min(1, 'Password is required'),
  mfaCode: z.string().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

// ---------------------------------------------------------------------------
// Component Props
// ---------------------------------------------------------------------------

interface LoginFormProps {
  onSuccess: (data?: unknown) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function LoginForm({ onSuccess }: LoginFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showMfaField, setShowMfaField] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    mode: 'onSubmit',
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const payload: Record<string, string> = {
        email: data.email,
        password: data.password,
      };

      if (showMfaField && data.mfaCode) {
        payload.mfa_code = data.mfaCode;
      }

      const response = await axios.post('/auth/login', payload);

      // Successful login
      onSuccess(response.data);
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const axiosError = error as AxiosError<{
          detail?: string;
          mfa_required?: boolean;
        }>;

        // Check for MFA requirement
        if (
          axiosError.response?.status === 403 &&
          axiosError.response.data?.mfa_required
        ) {
          setShowMfaField(true);
          setErrorMessage('Please enter your MFA code');
        } else {
          // Other errors
          setErrorMessage(
            axiosError.response?.data?.detail ||
              'Login failed. Please check your credentials.'
          );
        }
      } else {
        setErrorMessage('An unexpected error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      {/* Error Alert */}
      {errorMessage && (
        <div
          role="alert"
          className="rounded-md bg-red-50 p-4 text-sm text-red-800"
        >
          {errorMessage}
        </div>
      )}

      {/* Email Field */}
      <div>
        <label
          htmlFor="email"
          className="block text-sm font-medium text-gray-700"
        >
          Email
        </label>
        <input
          id="email"
          type="email"
          {...register('email', {
            onChange: () => {
              if (errorMessage) {
                setErrorMessage(null);
              }
            },
          })}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
        />
        {errors.email && (
          <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
        )}
      </div>

      {/* Password Field */}
      <div>
        <label
          htmlFor="password"
          className="block text-sm font-medium text-gray-700"
        >
          Password
        </label>
        <input
          id="password"
          type="password"
          {...register('password', {
            onChange: () => {
              if (errorMessage) {
                setErrorMessage(null);
              }
            },
          })}
          className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
        />
        {errors.password && (
          <p className="mt-1 text-sm text-red-600">{errors.password.message}</p>
        )}
      </div>

      {/* MFA Code Field (conditional) */}
      {showMfaField && (
        <div>
          <label
            htmlFor="mfaCode"
            className="block text-sm font-medium text-gray-700"
          >
            MFA Code
          </label>
          <input
            id="mfaCode"
            type="text"
            placeholder="Enter 6-digit code"
            {...register('mfaCode')}
            className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500 sm:text-sm"
            maxLength={6}
          />
          {errors.mfaCode && (
            <p className="mt-1 text-sm text-red-600">{errors.mfaCode.message}</p>
          )}
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isLoading ? 'Signing in...' : 'Sign In'}
      </button>
    </form>
  );
}
