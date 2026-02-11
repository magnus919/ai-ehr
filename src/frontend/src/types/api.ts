// =============================================================================
// API Response Types
// =============================================================================

/**
 * Standard paginated response from the API.
 */
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

/**
 * Standard API error response.
 */
export interface ApiError {
  status: number;
  code: string;
  message: string;
  details?: Record<string, string[]>;
  timestamp: string;
  path?: string;
  traceId?: string;
}

/**
 * Validation error for form fields.
 */
export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

/**
 * Standard API success response for mutations.
 */
export interface ApiResponse<T = void> {
  data: T;
  message?: string;
}

/**
 * Authentication response.
 */
export interface AuthResponse {
  user: import('./index').User;
  tokens: import('./index').AuthTokens;
}

/**
 * MFA challenge response (returned when MFA is required).
 */
export interface MFAChallengeResponse {
  mfaRequired: true;
  mfaToken: string;
  methods: ('totp' | 'sms' | 'email')[];
}

/**
 * Token refresh response.
 */
export interface TokenRefreshResponse {
  accessToken: string;
  expiresIn: number;
}

/**
 * Search/autocomplete result.
 */
export interface SearchResult<T = unknown> {
  items: T[];
  total: number;
  query: string;
}

/**
 * Bulk operation result.
 */
export interface BulkOperationResult {
  succeeded: number;
  failed: number;
  errors: Array<{
    index: number;
    id?: string;
    error: string;
  }>;
}

/**
 * File upload response.
 */
export interface FileUploadResponse {
  id: string;
  filename: string;
  mimeType: string;
  size: number;
  url: string;
}

/**
 * ICD-10 code search result.
 */
export interface ICD10Code {
  code: string;
  description: string;
  category: string;
  isLeaf: boolean;
}

/**
 * Medication search result (for autocomplete).
 */
export interface MedicationSearchResult {
  rxcui: string;
  name: string;
  tty: string;
  strength?: string;
  doseForm?: string;
}

/**
 * Drug interaction check result.
 */
export interface DrugInteractionCheckResult {
  hasInteractions: boolean;
  interactions: Array<{
    severity: 'high' | 'moderate' | 'low';
    drug1: string;
    drug2: string;
    description: string;
    recommendation: string;
    source: string;
  }>;
}

/**
 * Provider availability slot.
 */
export interface AvailabilitySlot {
  start: string;
  end: string;
  available: boolean;
  providerId: string;
  providerName: string;
  location?: string;
}

/**
 * Dashboard statistics.
 */
export interface DashboardStats {
  todayAppointments: number;
  checkedIn: number;
  pendingOrders: number;
  unreadMessages: number;
  recentPatients: number;
  criticalAlerts: number;
}

/**
 * Request params for list endpoints.
 */
export interface ListParams {
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  search?: string;
}
