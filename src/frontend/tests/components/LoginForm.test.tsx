/**
 * Tests for the LoginForm component.
 *
 * Covers:
 *   - Form validation (email format, password required)
 *   - Successful form submission
 *   - Error display for invalid credentials
 *   - MFA code field (shown when required)
 *   - Accessibility
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { http, HttpResponse } from "msw";

import { server } from "../setup";

// ---------------------------------------------------------------------------
// Component import
// ---------------------------------------------------------------------------
import LoginForm from "@components/LoginForm";

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
}

function renderLoginForm(props = {}) {
  const queryClient = createTestQueryClient();
  const onSuccess = vi.fn();

  const result = render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <LoginForm onSuccess={onSuccess} {...props} />
      </BrowserRouter>
    </QueryClientProvider>
  );

  return { ...result, onSuccess };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("LoginForm", () => {
  describe("rendering", () => {
    it("renders email and password fields", () => {
      renderLoginForm();

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    });

    it("renders a submit button", () => {
      renderLoginForm();

      expect(
        screen.getByRole("button", { name: /sign in|log in|submit/i })
      ).toBeInTheDocument();
    });

    it("email field has correct input type", () => {
      renderLoginForm();

      const emailInput = screen.getByLabelText(/email/i);
      expect(emailInput).toHaveAttribute("type", "email");
    });

    it("password field has correct input type", () => {
      renderLoginForm();

      const passwordInput = screen.getByLabelText(/password/i);
      expect(passwordInput).toHaveAttribute("type", "password");
    });
  });

  describe("validation", () => {
    it("shows error when email is empty on submit", async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const submitButton = screen.getByRole("button", {
        name: /sign in|log in|submit/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/email.*required|enter.*email/i)
        ).toBeInTheDocument();
      });
    });

    it("shows error when password is empty on submit", async () => {
      const user = userEvent.setup();
      renderLoginForm();

      // Fill email but leave password empty
      const emailInput = screen.getByLabelText(/email/i);
      await user.type(emailInput, "test@example.com");

      const submitButton = screen.getByRole("button", {
        name: /sign in|log in|submit/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/password.*required|enter.*password/i)
        ).toBeInTheDocument();
      });
    });

    it("shows error for invalid email format", async () => {
      const user = userEvent.setup();
      renderLoginForm();

      const emailInput = screen.getByLabelText(/email/i);
      await user.type(emailInput, "not-an-email");

      const passwordInput = screen.getByLabelText(/password/i);
      await user.type(passwordInput, "SomePass123!");

      const submitButton = screen.getByRole("button", {
        name: /sign in|log in|submit/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/valid.*email|invalid.*email/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe("form submission", () => {
    it("calls onSuccess after successful login", async () => {
      const user = userEvent.setup();
      const { onSuccess } = renderLoginForm();

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);

      await user.type(emailInput, "test@example.com");
      await user.type(passwordInput, "ValidPass1!");

      const submitButton = screen.getByRole("button", {
        name: /sign in|log in|submit/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalledTimes(1);
      });
    });

    it("disables submit button during loading", async () => {
      const user = userEvent.setup();

      // Add a delay to the login handler
      server.use(
        http.post("/auth/login", async () => {
          await new Promise((resolve) => setTimeout(resolve, 500));
          return HttpResponse.json({
            access_token: "tok",
            refresh_token: "ref",
            token_type: "bearer",
          });
        })
      );

      renderLoginForm();

      await user.type(screen.getByLabelText(/email/i), "test@example.com");
      await user.type(screen.getByLabelText(/password/i), "ValidPass1!");

      const submitButton = screen.getByRole("button", {
        name: /sign in|log in|submit/i,
      });
      await user.click(submitButton);

      // Button should be disabled or show loading state
      await waitFor(() => {
        expect(
          submitButton.hasAttribute("disabled") ||
            screen.queryByText(/loading|signing/i) !== null
        ).toBe(true);
      });
    });
  });

  describe("error display", () => {
    it("shows error message for invalid credentials", async () => {
      const user = userEvent.setup();
      renderLoginForm();

      await user.type(screen.getByLabelText(/email/i), "wrong@example.com");
      await user.type(screen.getByLabelText(/password/i), "WrongPass1!");

      const submitButton = screen.getByRole("button", {
        name: /sign in|log in|submit/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/invalid|incorrect|failed/i) ||
            screen.getByRole("alert")
        ).toBeInTheDocument();
      });
    });

    it("clears error when user starts typing again", async () => {
      const user = userEvent.setup();
      renderLoginForm();

      // Trigger an error
      await user.type(screen.getByLabelText(/email/i), "wrong@example.com");
      await user.type(screen.getByLabelText(/password/i), "WrongPass1!");
      await user.click(
        screen.getByRole("button", { name: /sign in|log in|submit/i })
      );

      await waitFor(() => {
        expect(
          screen.queryByText(/invalid|incorrect|failed/i) ||
            screen.queryByRole("alert")
        ).toBeInTheDocument();
      });

      // Start typing to clear the error
      await user.clear(screen.getByLabelText(/email/i));
      await user.type(screen.getByLabelText(/email/i), "new@example.com");

      // Error should be cleared or hidden
      await waitFor(() => {
        const alert = screen.queryByRole("alert");
        const errorText = screen.queryByText(/invalid|incorrect|failed/i);
        // At least one of them should be gone
        expect(alert === null || errorText === null).toBe(true);
      });
    });
  });

  describe("MFA field", () => {
    it("shows MFA code input when MFA is required", async () => {
      const user = userEvent.setup();

      server.use(
        http.post("/auth/login", () => {
          return HttpResponse.json(
            { detail: "MFA required", mfa_required: true },
            { status: 403 }
          );
        })
      );

      renderLoginForm();

      await user.type(screen.getByLabelText(/email/i), "mfa@example.com");
      await user.type(screen.getByLabelText(/password/i), "ValidPass1!");
      await user.click(
        screen.getByRole("button", { name: /sign in|log in|submit/i })
      );

      await waitFor(() => {
        expect(
          screen.getByLabelText(/mfa|verification|code/i) ||
            screen.getByPlaceholderText(/code|6.digit/i)
        ).toBeInTheDocument();
      });
    });

    it("MFA code field accepts 6 digits", async () => {
      const user = userEvent.setup();

      server.use(
        http.post("/auth/login", () => {
          return HttpResponse.json(
            { detail: "MFA required", mfa_required: true },
            { status: 403 }
          );
        })
      );

      renderLoginForm();

      await user.type(screen.getByLabelText(/email/i), "mfa@example.com");
      await user.type(screen.getByLabelText(/password/i), "ValidPass1!");
      await user.click(
        screen.getByRole("button", { name: /sign in|log in|submit/i })
      );

      await waitFor(() => {
        const mfaInput =
          screen.getByLabelText(/mfa|verification|code/i) ||
          screen.getByPlaceholderText(/code|6.digit/i);
        expect(mfaInput).toBeInTheDocument();
      });

      const mfaInput =
        screen.getByLabelText(/mfa|verification|code/i) ||
        screen.getByPlaceholderText(/code|6.digit/i);
      await user.type(mfaInput, "123456");
      expect(mfaInput).toHaveValue("123456");
    });
  });

  describe("accessibility", () => {
    it("form fields have associated labels", () => {
      renderLoginForm();

      const emailInput = screen.getByLabelText(/email/i);
      const passwordInput = screen.getByLabelText(/password/i);

      expect(emailInput).toHaveAccessibleName();
      expect(passwordInput).toHaveAccessibleName();
    });

    it("submit button has accessible name", () => {
      renderLoginForm();

      const submitButton = screen.getByRole("button", {
        name: /sign in|log in|submit/i,
      });
      expect(submitButton).toHaveAccessibleName();
    });
  });
});
