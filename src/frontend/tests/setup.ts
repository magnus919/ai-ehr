/**
 * Vitest setup file for OpenMedRecord frontend tests.
 *
 * Configures:
 *   - @testing-library/jest-dom matchers
 *   - MSW (Mock Service Worker) for API mocking
 *   - Global test utilities and cleanup
 */

import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";
import { setupServer } from "msw/node";
import { http, HttpResponse } from "msw";

// ---------------------------------------------------------------------------
// MSW Handlers -- Default API mocks for all tests
// ---------------------------------------------------------------------------

export const TEST_PATIENTS = [
  {
    id: "p-001",
    first_name: "Jane",
    last_name: "Doe",
    date_of_birth: "1985-06-15",
    gender: "female",
    mrn: "MRN-00001",
    email: "jane.doe@example.com",
    phone: "+15551234567",
    is_active: true,
  },
  {
    id: "p-002",
    first_name: "John",
    last_name: "Smith",
    date_of_birth: "1970-03-22",
    gender: "male",
    mrn: "MRN-00002",
    email: "john.smith@example.com",
    phone: "+15559876543",
    is_active: true,
  },
  {
    id: "p-003",
    first_name: "Maria",
    last_name: "Garcia",
    date_of_birth: "1992-11-08",
    gender: "female",
    mrn: "MRN-00003",
    email: "maria.garcia@example.com",
    phone: "+15555551234",
    is_active: true,
  },
];

export const TEST_USER = {
  id: "u-001",
  email: "test.clinician@openmedrecord.health",
  first_name: "Test",
  last_name: "Clinician",
  role: "physician",
};

export const handlers = [
  // -- Auth endpoints -------------------------------------------------------
  http.post("/auth/login", async ({ request }) => {
    const body = (await request.json()) as Record<string, string>;
    if (
      body.email === "test@example.com" &&
      body.password === "ValidPass1!"
    ) {
      return HttpResponse.json({
        access_token: "mock-access-token",
        refresh_token: "mock-refresh-token",
        token_type: "bearer",
        user: TEST_USER,
      });
    }
    return HttpResponse.json(
      { detail: "Invalid email or password" },
      { status: 401 }
    );
  }),

  http.get("/auth/me", () => {
    return HttpResponse.json(TEST_USER);
  }),

  // -- Patient endpoints ----------------------------------------------------
  http.get("/api/v1/patients", ({ request }) => {
    const url = new URL(request.url);
    const search = url.searchParams.get("search") || "";
    const page = parseInt(url.searchParams.get("page") || "1", 10);
    const pageSize = parseInt(url.searchParams.get("page_size") || "20", 10);

    let filtered = TEST_PATIENTS;
    if (search) {
      const q = search.toLowerCase();
      filtered = TEST_PATIENTS.filter(
        (p) =>
          p.first_name.toLowerCase().includes(q) ||
          p.last_name.toLowerCase().includes(q) ||
          p.mrn.toLowerCase().includes(q)
      );
    }

    return HttpResponse.json({
      items: filtered.slice((page - 1) * pageSize, page * pageSize),
      total: filtered.length,
      page,
      page_size: pageSize,
      pages: Math.ceil(filtered.length / pageSize),
    });
  }),

  http.get("/api/v1/patients/:id", ({ params }) => {
    const patient = TEST_PATIENTS.find((p) => p.id === params.id);
    if (patient) {
      return HttpResponse.json(patient);
    }
    return HttpResponse.json(
      { detail: "Patient not found" },
      { status: 404 }
    );
  }),

  http.post("/api/v1/patients", async ({ request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    return HttpResponse.json(
      {
        id: "p-new",
        ...body,
        is_active: true,
      },
      { status: 201 }
    );
  }),

  http.put("/api/v1/patients/:id", async ({ params, request }) => {
    const body = (await request.json()) as Record<string, unknown>;
    const patient = TEST_PATIENTS.find((p) => p.id === params.id);
    if (patient) {
      return HttpResponse.json({ ...patient, ...body });
    }
    return HttpResponse.json(
      { detail: "Patient not found" },
      { status: 404 }
    );
  }),
];

// ---------------------------------------------------------------------------
// MSW Server Setup
// ---------------------------------------------------------------------------

export const server = setupServer(...handlers);

beforeAll(() => {
  server.listen({ onUnhandledRequest: "warn" });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});
