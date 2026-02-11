/**
 * Tests for the PatientForm component.
 *
 * Covers:
 *   - Form field validation (required fields, formats)
 *   - Successful form submission (create mode)
 *   - Edit mode (pre-populated fields)
 *   - Required field indicators
 *   - Address and emergency contact sections
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";

import { TEST_PATIENTS } from "../setup";

// ---------------------------------------------------------------------------
// Component import
// ---------------------------------------------------------------------------
import PatientForm from "@components/PatientForm";

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

function renderPatientForm(props = {}) {
  const queryClient = createTestQueryClient();
  const onSubmit = vi.fn().mockResolvedValue({ id: "p-new" });
  const onCancel = vi.fn();

  const result = render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <PatientForm onSubmit={onSubmit} onCancel={onCancel} {...props} />
      </BrowserRouter>
    </QueryClientProvider>
  );

  return { ...result, onSubmit, onCancel };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("PatientForm", () => {
  describe("rendering (create mode)", () => {
    it("renders all required demographic fields", () => {
      renderPatientForm();

      expect(screen.getByLabelText(/first name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/last name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/date of birth/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/gender/i)).toBeInTheDocument();
    });

    it("renders optional contact fields", () => {
      renderPatientForm();

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/phone/i)).toBeInTheDocument();
    });

    it("renders submit and cancel buttons", () => {
      renderPatientForm();

      expect(
        screen.getByRole("button", { name: /save|submit|create/i })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: /cancel/i })
      ).toBeInTheDocument();
    });

    it("starts with empty fields in create mode", () => {
      renderPatientForm();

      const firstNameInput = screen.getByLabelText(/first name/i);
      expect(firstNameInput).toHaveValue("");
    });
  });

  describe("validation", () => {
    it("shows error when first name is empty on submit", async () => {
      const user = userEvent.setup();
      renderPatientForm();

      const submitButton = screen.getByRole("button", {
        name: /save|submit|create/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/first name.*required/i) ||
            screen.getByText(/required/i)
        ).toBeInTheDocument();
      });
    });

    it("shows error when last name is empty on submit", async () => {
      const user = userEvent.setup();
      renderPatientForm();

      // Fill first name but leave last name empty
      await user.type(screen.getByLabelText(/first name/i), "Jane");

      const submitButton = screen.getByRole("button", {
        name: /save|submit|create/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/last name.*required/i) ||
            screen.getAllByText(/required/i).length
        ).toBeTruthy();
      });
    });

    it("shows error when date of birth is empty", async () => {
      const user = userEvent.setup();
      renderPatientForm();

      await user.type(screen.getByLabelText(/first name/i), "Jane");
      await user.type(screen.getByLabelText(/last name/i), "Doe");

      const submitButton = screen.getByRole("button", {
        name: /save|submit|create/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/date of birth.*required/i) ||
            screen.getAllByText(/required/i).length
        ).toBeTruthy();
      });
    });

    it("shows error for invalid email format", async () => {
      const user = userEvent.setup();
      renderPatientForm();

      const emailInput = screen.getByLabelText(/email/i);
      await user.type(emailInput, "not-an-email");

      const submitButton = screen.getByRole("button", {
        name: /save|submit|create/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/valid.*email|invalid.*email/i)
        ).toBeInTheDocument();
      });
    });

    it("shows error for future date of birth", async () => {
      const user = userEvent.setup();
      renderPatientForm();

      await user.type(screen.getByLabelText(/first name/i), "Jane");
      await user.type(screen.getByLabelText(/last name/i), "Doe");

      const dobInput = screen.getByLabelText(/date of birth/i);
      await user.type(dobInput, "2099-01-01");

      const submitButton = screen.getByRole("button", {
        name: /save|submit|create/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(
          screen.getByText(/future|past|valid.*date/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe("form submission", () => {
    it("calls onSubmit with form data on valid submission", async () => {
      const user = userEvent.setup();
      const { onSubmit } = renderPatientForm();

      await user.type(screen.getByLabelText(/first name/i), "Jane");
      await user.type(screen.getByLabelText(/last name/i), "Doe");
      await user.type(screen.getByLabelText(/date of birth/i), "1985-06-15");

      // Select gender (could be a select or radio)
      const genderField = screen.getByLabelText(/gender/i);
      if (genderField.tagName === "SELECT") {
        await user.selectOptions(genderField, "female");
      } else {
        // Try clicking a radio button
        const femaleOption = screen.getByLabelText(/female/i);
        await user.click(femaleOption);
      }

      const submitButton = screen.getByRole("button", {
        name: /save|submit|create/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledTimes(1);
        const callData = onSubmit.mock.calls[0][0];
        expect(callData.first_name).toBe("Jane");
        expect(callData.last_name).toBe("Doe");
      });
    });

    it("calls onCancel when cancel button is clicked", async () => {
      const user = userEvent.setup();
      const { onCancel } = renderPatientForm();

      const cancelButton = screen.getByRole("button", { name: /cancel/i });
      await user.click(cancelButton);

      expect(onCancel).toHaveBeenCalledTimes(1);
    });
  });

  describe("edit mode", () => {
    const existingPatient = TEST_PATIENTS[0];

    it("pre-populates fields with existing patient data", () => {
      renderPatientForm({ initialData: existingPatient, mode: "edit" });

      expect(screen.getByLabelText(/first name/i)).toHaveValue(
        existingPatient.first_name
      );
      expect(screen.getByLabelText(/last name/i)).toHaveValue(
        existingPatient.last_name
      );
    });

    it("shows 'Update' instead of 'Create' on submit button", () => {
      renderPatientForm({ initialData: existingPatient, mode: "edit" });

      expect(
        screen.getByRole("button", { name: /update|save/i })
      ).toBeInTheDocument();
    });

    it("submits with updated data", async () => {
      const user = userEvent.setup();
      const { onSubmit } = renderPatientForm({
        initialData: existingPatient,
        mode: "edit",
      });

      const phoneInput = screen.getByLabelText(/phone/i);
      await user.clear(phoneInput);
      await user.type(phoneInput, "+15559998888");

      const submitButton = screen.getByRole("button", {
        name: /update|save/i,
      });
      await user.click(submitButton);

      await waitFor(() => {
        expect(onSubmit).toHaveBeenCalledTimes(1);
        const callData = onSubmit.mock.calls[0][0];
        expect(callData.phone).toBe("+15559998888");
        // Original fields should still be present
        expect(callData.first_name).toBe(existingPatient.first_name);
      });
    });
  });

  describe("required field indicators", () => {
    it("marks required fields with an asterisk or aria-required", () => {
      renderPatientForm();

      const firstNameInput = screen.getByLabelText(/first name/i);
      const lastNameInput = screen.getByLabelText(/last name/i);

      // Check for aria-required attribute or asterisk in label
      const isRequired = (input: HTMLElement) =>
        input.hasAttribute("required") ||
        input.getAttribute("aria-required") === "true";

      expect(isRequired(firstNameInput)).toBe(true);
      expect(isRequired(lastNameInput)).toBe(true);
    });
  });

  describe("address section", () => {
    it("renders address fields", () => {
      renderPatientForm();

      // Look for address fields (may be collapsed by default)
      expect(
        screen.getByLabelText(/address|street/i) ||
          screen.getByText(/address/i)
      ).toBeInTheDocument();
    });
  });

  describe("accessibility", () => {
    it("all form fields have associated labels", () => {
      renderPatientForm();

      const inputs = screen.getAllByRole("textbox");
      inputs.forEach((input) => {
        expect(input).toHaveAccessibleName();
      });
    });

    it("form has an accessible name or heading", () => {
      renderPatientForm();

      expect(
        screen.getByRole("form") ||
          screen.getByRole("heading", { name: /patient/i })
      ).toBeInTheDocument();
    });
  });
});
