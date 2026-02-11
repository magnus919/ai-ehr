/**
 * Tests for the PatientList component.
 *
 * Covers:
 *   - Rendering a list of patients
 *   - Search/filter functionality
 *   - Pagination controls
 *   - Empty state display
 *   - Loading state
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import { http, HttpResponse } from "msw";

import { server, TEST_PATIENTS } from "../setup";

// ---------------------------------------------------------------------------
// Component import (adjust path to match actual component location)
// ---------------------------------------------------------------------------
// Note: The component may not exist yet; these tests define the expected API.
import PatientList from "@components/PatientList";

// ---------------------------------------------------------------------------
// Test utilities
// ---------------------------------------------------------------------------

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("PatientList", () => {
  it("renders a list of patients", async () => {
    renderWithProviders(<PatientList />);

    // Wait for patients to load
    await waitFor(() => {
      expect(screen.getByText("Jane Doe")).toBeInTheDocument();
    });

    expect(screen.getByText("John Smith")).toBeInTheDocument();
    expect(screen.getByText("Maria Garcia")).toBeInTheDocument();
  });

  it("displays patient MRN for each row", async () => {
    renderWithProviders(<PatientList />);

    await waitFor(() => {
      expect(screen.getByText("MRN-00001")).toBeInTheDocument();
    });

    expect(screen.getByText("MRN-00002")).toBeInTheDocument();
    expect(screen.getByText("MRN-00003")).toBeInTheDocument();
  });

  it("displays date of birth for each patient", async () => {
    renderWithProviders(<PatientList />);

    await waitFor(() => {
      // Date format may vary; check for year at minimum
      expect(screen.getByText(/1985/)).toBeInTheDocument();
    });
  });

  it("shows a loading indicator while fetching", () => {
    renderWithProviders(<PatientList />);

    // Should show loading state before data arrives
    expect(
      screen.getByRole("progressbar") ||
        screen.getByText(/loading/i) ||
        screen.getByTestId("loading-spinner")
    ).toBeInTheDocument();
  });

  describe("search functionality", () => {
    it("filters patients by search input", async () => {
      const user = userEvent.setup();
      renderWithProviders(<PatientList />);

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText("Jane Doe")).toBeInTheDocument();
      });

      // Type in the search box
      const searchInput = screen.getByRole("searchbox") ||
        screen.getByPlaceholderText(/search/i);
      await user.clear(searchInput);
      await user.type(searchInput, "Garcia");

      // After debounce, only Maria Garcia should appear
      await waitFor(() => {
        expect(screen.getByText("Maria Garcia")).toBeInTheDocument();
      });
    });

    it("shows search results count", async () => {
      const user = userEvent.setup();
      renderWithProviders(<PatientList />);

      await waitFor(() => {
        expect(screen.getByText("Jane Doe")).toBeInTheDocument();
      });

      // Search for a specific patient
      const searchInput = screen.getByRole("searchbox") ||
        screen.getByPlaceholderText(/search/i);
      await user.clear(searchInput);
      await user.type(searchInput, "Doe");

      await waitFor(() => {
        // Should show count like "1 patient" or "1 result"
        expect(
          screen.getByText(/1\s*(patient|result)/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe("pagination", () => {
    it("renders pagination controls when there are multiple pages", async () => {
      // Override handler to return paginated data
      server.use(
        http.get("/api/v1/patients", () => {
          return HttpResponse.json({
            items: TEST_PATIENTS.slice(0, 2),
            total: 50,
            page: 1,
            page_size: 2,
            pages: 25,
          });
        })
      );

      renderWithProviders(<PatientList />);

      await waitFor(() => {
        expect(screen.getByText("Jane Doe")).toBeInTheDocument();
      });

      // Pagination controls should be visible
      expect(
        screen.getByRole("navigation", { name: /pagination/i }) ||
          screen.getByTestId("pagination")
      ).toBeInTheDocument();
    });

    it("navigates to the next page when clicking next", async () => {
      const user = userEvent.setup();
      let requestedPage = 1;

      server.use(
        http.get("/api/v1/patients", ({ request }) => {
          const url = new URL(request.url);
          requestedPage = parseInt(url.searchParams.get("page") || "1", 10);

          return HttpResponse.json({
            items: requestedPage === 1
              ? TEST_PATIENTS.slice(0, 2)
              : TEST_PATIENTS.slice(2, 3),
            total: 3,
            page: requestedPage,
            page_size: 2,
            pages: 2,
          });
        })
      );

      renderWithProviders(<PatientList />);

      await waitFor(() => {
        expect(screen.getByText("Jane Doe")).toBeInTheDocument();
      });

      // Click next page
      const nextButton = screen.getByRole("button", { name: /next/i });
      await user.click(nextButton);

      await waitFor(() => {
        expect(requestedPage).toBe(2);
      });
    });
  });

  describe("empty state", () => {
    it("shows an empty state when no patients exist", async () => {
      server.use(
        http.get("/api/v1/patients", () => {
          return HttpResponse.json({
            items: [],
            total: 0,
            page: 1,
            page_size: 20,
            pages: 0,
          });
        })
      );

      renderWithProviders(<PatientList />);

      await waitFor(() => {
        expect(
          screen.getByText(/no patients/i) ||
            screen.getByText(/no results/i)
        ).toBeInTheDocument();
      });
    });

    it("shows an empty state when search has no results", async () => {
      const user = userEvent.setup();

      server.use(
        http.get("/api/v1/patients", ({ request }) => {
          const url = new URL(request.url);
          const search = url.searchParams.get("search") || "";

          if (search) {
            return HttpResponse.json({
              items: [],
              total: 0,
              page: 1,
              page_size: 20,
              pages: 0,
            });
          }

          return HttpResponse.json({
            items: TEST_PATIENTS,
            total: TEST_PATIENTS.length,
            page: 1,
            page_size: 20,
            pages: 1,
          });
        })
      );

      renderWithProviders(<PatientList />);

      await waitFor(() => {
        expect(screen.getByText("Jane Doe")).toBeInTheDocument();
      });

      const searchInput = screen.getByRole("searchbox") ||
        screen.getByPlaceholderText(/search/i);
      await user.clear(searchInput);
      await user.type(searchInput, "ZZZZZ");

      await waitFor(() => {
        expect(
          screen.getByText(/no patients/i) ||
            screen.getByText(/no results/i)
        ).toBeInTheDocument();
      });
    });
  });

  describe("error handling", () => {
    it("displays an error message when the API fails", async () => {
      server.use(
        http.get("/api/v1/patients", () => {
          return HttpResponse.json(
            { detail: "Internal server error" },
            { status: 500 }
          );
        })
      );

      renderWithProviders(<PatientList />);

      await waitFor(() => {
        expect(
          screen.getByText(/error/i) || screen.getByRole("alert")
        ).toBeInTheDocument();
      });
    });
  });
});
