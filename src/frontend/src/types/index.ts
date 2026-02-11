// =============================================================================
// OpenMedRecord - Core TypeScript Interfaces
// Aligned with FHIR R4 resource structures and backend schemas
// =============================================================================

/** ISO 8601 date string (YYYY-MM-DD) */
export type DateString = string;

/** ISO 8601 datetime string */
export type DateTimeString = string;

/** UUID string */
export type UUID = string;

// -----------------------------------------------------------------------------
// Enums
// -----------------------------------------------------------------------------

export enum Gender {
  Male = 'male',
  Female = 'female',
  Other = 'other',
  Unknown = 'unknown',
}

export enum PatientStatus {
  Active = 'active',
  Inactive = 'inactive',
  Deceased = 'deceased',
}

export enum EncounterStatus {
  Planned = 'planned',
  InProgress = 'in-progress',
  OnLeave = 'on-leave',
  Finished = 'finished',
  Cancelled = 'cancelled',
  EnteredInError = 'entered-in-error',
}

export enum EncounterClass {
  Ambulatory = 'AMB',
  Emergency = 'EMER',
  Inpatient = 'IMP',
  Observation = 'OBSENC',
  Virtual = 'VR',
}

export enum ObservationStatus {
  Registered = 'registered',
  Preliminary = 'preliminary',
  Final = 'final',
  Amended = 'amended',
  Corrected = 'corrected',
  Cancelled = 'cancelled',
  EnteredInError = 'entered-in-error',
}

export enum ConditionClinicalStatus {
  Active = 'active',
  Recurrence = 'recurrence',
  Relapse = 'relapse',
  Inactive = 'inactive',
  Remission = 'remission',
  Resolved = 'resolved',
}

export enum MedicationRequestStatus {
  Active = 'active',
  OnHold = 'on-hold',
  Ended = 'ended',
  Stopped = 'stopped',
  Completed = 'completed',
  Cancelled = 'cancelled',
  EnteredInError = 'entered-in-error',
  Draft = 'draft',
}

export enum OrderType {
  Medication = 'medication',
  Laboratory = 'laboratory',
  Imaging = 'imaging',
  Procedure = 'procedure',
  Referral = 'referral',
}

export enum OrderStatus {
  Draft = 'draft',
  Active = 'active',
  Completed = 'completed',
  Cancelled = 'cancelled',
  OnHold = 'on-hold',
}

export enum OrderPriority {
  Routine = 'routine',
  Urgent = 'urgent',
  ASAP = 'asap',
  STAT = 'stat',
}

export enum AppointmentStatus {
  Proposed = 'proposed',
  Pending = 'pending',
  Booked = 'booked',
  Arrived = 'arrived',
  Fulfilled = 'fulfilled',
  Cancelled = 'cancelled',
  NoShow = 'noshow',
  CheckedIn = 'checked-in',
}

export enum AppointmentType {
  Routine = 'routine',
  WalkIn = 'walkin',
  Checkup = 'checkup',
  FollowUp = 'followup',
  Emergency = 'emergency',
}

export enum UserRole {
  Admin = 'admin',
  Physician = 'physician',
  Nurse = 'nurse',
  MedicalAssistant = 'medical_assistant',
  FrontDesk = 'front_desk',
  Billing = 'billing',
  LabTech = 'lab_tech',
  Pharmacist = 'pharmacist',
}

export enum AuditAction {
  Create = 'create',
  Read = 'read',
  Update = 'update',
  Delete = 'delete',
  Login = 'login',
  Logout = 'logout',
  Export = 'export',
  Print = 'print',
}

// -----------------------------------------------------------------------------
// Core Domain Models
// -----------------------------------------------------------------------------

export interface HumanName {
  use?: 'official' | 'usual' | 'nickname' | 'maiden';
  family: string;
  given: string[];
  prefix?: string[];
  suffix?: string[];
}

export interface Address {
  use?: 'home' | 'work' | 'temp' | 'billing';
  line1: string;
  line2?: string;
  city: string;
  state: string;
  postalCode: string;
  country: string;
}

export interface ContactPoint {
  system: 'phone' | 'fax' | 'email' | 'sms';
  value: string;
  use?: 'home' | 'work' | 'mobile';
}

export interface CodeableConcept {
  coding: Array<{
    system: string;
    code: string;
    display: string;
  }>;
  text?: string;
}

export interface Reference {
  reference: string;
  display?: string;
  type?: string;
}

export interface Period {
  start: DateTimeString;
  end?: DateTimeString;
}

export interface Insurance {
  provider: string;
  planName: string;
  memberId: string;
  groupNumber?: string;
  effectiveDate: DateString;
  expirationDate?: DateString;
}

export interface EmergencyContact {
  name: string;
  relationship: string;
  phone: string;
  email?: string;
}

// -----------------------------------------------------------------------------
// Patient
// -----------------------------------------------------------------------------

export interface Patient {
  id: UUID;
  mrn: string;
  active: boolean;
  name: HumanName;
  gender: Gender;
  birthDate: DateString;
  deceasedBoolean?: boolean;
  deceasedDateTime?: DateTimeString;
  address?: Address[];
  telecom?: ContactPoint[];
  maritalStatus?: string;
  language?: string;
  race?: string;
  ethnicity?: string;
  ssn?: string;
  insurance?: Insurance[];
  emergencyContacts?: EmergencyContact[];
  generalPractitioner?: Reference;
  photo?: string;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
}

export interface PatientCreateInput {
  name: HumanName;
  gender: Gender;
  birthDate: DateString;
  address?: Address[];
  telecom?: ContactPoint[];
  maritalStatus?: string;
  language?: string;
  race?: string;
  ethnicity?: string;
  ssn?: string;
  insurance?: Insurance[];
  emergencyContacts?: EmergencyContact[];
}

export interface PatientUpdateInput extends Partial<PatientCreateInput> {
  active?: boolean;
}

export interface PatientSearchParams {
  query?: string;
  name?: string;
  mrn?: string;
  birthDate?: DateString;
  gender?: Gender;
  active?: boolean;
  page?: number;
  pageSize?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

// -----------------------------------------------------------------------------
// Encounter
// -----------------------------------------------------------------------------

export interface VitalSigns {
  temperature?: number;
  temperatureUnit?: 'F' | 'C';
  heartRate?: number;
  respiratoryRate?: number;
  bloodPressureSystolic?: number;
  bloodPressureDiastolic?: number;
  oxygenSaturation?: number;
  weight?: number;
  weightUnit?: 'kg' | 'lb';
  height?: number;
  heightUnit?: 'cm' | 'in';
  bmi?: number;
  painLevel?: number;
}

export interface SOAPNote {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
}

export interface Encounter {
  id: UUID;
  status: EncounterStatus;
  class: EncounterClass;
  type?: CodeableConcept[];
  subject: Reference;
  participant?: Array<{
    individual: Reference;
    type?: string;
  }>;
  period: Period;
  reasonCode?: CodeableConcept[];
  diagnosis?: Array<{
    condition: Reference;
    rank?: number;
  }>;
  location?: Reference;
  serviceProvider?: Reference;
  vitalSigns?: VitalSigns;
  soapNote?: SOAPNote;
  chiefComplaint?: string;
  notes?: string;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
}

export interface EncounterCreateInput {
  class: EncounterClass;
  patientId: UUID;
  providerId?: UUID;
  type?: CodeableConcept[];
  reasonCode?: CodeableConcept[];
  chiefComplaint?: string;
  scheduledStart?: DateTimeString;
}

export interface EncounterUpdateInput {
  status?: EncounterStatus;
  vitalSigns?: VitalSigns;
  soapNote?: SOAPNote;
  diagnosis?: Array<{
    conditionId?: UUID;
    code: string;
    display: string;
    rank?: number;
  }>;
  notes?: string;
}

// -----------------------------------------------------------------------------
// Observation (Lab Results, Vitals, etc.)
// -----------------------------------------------------------------------------

export interface Observation {
  id: UUID;
  status: ObservationStatus;
  category?: CodeableConcept[];
  code: CodeableConcept;
  subject: Reference;
  encounter?: Reference;
  effectiveDateTime?: DateTimeString;
  issued?: DateTimeString;
  performer?: Reference[];
  valueQuantity?: {
    value: number;
    unit: string;
    system?: string;
    code?: string;
  };
  valueString?: string;
  valueCodeableConcept?: CodeableConcept;
  interpretation?: CodeableConcept[];
  referenceRange?: Array<{
    low?: { value: number; unit: string };
    high?: { value: number; unit: string };
    text?: string;
  }>;
  note?: string;
  createdAt: DateTimeString;
}

// -----------------------------------------------------------------------------
// Condition (Diagnoses / Problem List)
// -----------------------------------------------------------------------------

export interface Condition {
  id: UUID;
  clinicalStatus: ConditionClinicalStatus;
  verificationStatus?: 'unconfirmed' | 'provisional' | 'differential' | 'confirmed';
  category?: CodeableConcept[];
  severity?: CodeableConcept;
  code: CodeableConcept;
  subject: Reference;
  encounter?: Reference;
  onsetDateTime?: DateTimeString;
  abatementDateTime?: DateTimeString;
  recordedDate?: DateTimeString;
  recorder?: Reference;
  note?: string;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
}

// -----------------------------------------------------------------------------
// MedicationRequest
// -----------------------------------------------------------------------------

export interface Dosage {
  text?: string;
  timing?: string;
  route?: CodeableConcept;
  doseQuantity?: {
    value: number;
    unit: string;
  };
  frequency?: string;
  period?: string;
  asNeeded?: boolean;
  maxDosePerPeriod?: string;
}

export interface MedicationRequest {
  id: UUID;
  status: MedicationRequestStatus;
  intent: 'order' | 'plan' | 'proposal';
  medicationCodeableConcept: CodeableConcept;
  subject: Reference;
  encounter?: Reference;
  authoredOn: DateTimeString;
  requester: Reference;
  dosageInstruction?: Dosage[];
  dispenseRequest?: {
    numberOfRepeatsAllowed?: number;
    quantity?: { value: number; unit: string };
    expectedSupplyDuration?: { value: number; unit: string };
  };
  substitution?: {
    allowedBoolean: boolean;
    reason?: CodeableConcept;
  };
  note?: string;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
}

// -----------------------------------------------------------------------------
// Order (Composite order type for labs, imaging, referrals, medications)
// -----------------------------------------------------------------------------

export interface Order {
  id: UUID;
  type: OrderType;
  status: OrderStatus;
  priority: OrderPriority;
  code: CodeableConcept;
  subject: Reference;
  encounter?: Reference;
  requester: Reference;
  performer?: Reference;
  authoredOn: DateTimeString;
  occurrence?: DateTimeString;
  reasonCode?: CodeableConcept[];
  note?: string;
  results?: Reference[];
  medicationDetails?: {
    dosage: Dosage[];
    dispenseQuantity?: number;
    refills?: number;
    pharmacy?: string;
  };
  imagingDetails?: {
    bodysite?: CodeableConcept;
    contrast?: boolean;
    instructions?: string;
  };
  labDetails?: {
    specimenType?: string;
    fastingRequired?: boolean;
    instructions?: string;
  };
  alerts?: DrugInteractionAlert[];
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
}

export interface DrugInteractionAlert {
  severity: 'high' | 'moderate' | 'low';
  description: string;
  interactingDrug: string;
  recommendation: string;
}

export interface OrderCreateInput {
  type: OrderType;
  priority: OrderPriority;
  code: CodeableConcept;
  patientId: UUID;
  encounterId?: UUID;
  reasonCode?: CodeableConcept[];
  note?: string;
  occurrence?: DateTimeString;
  medicationDetails?: Order['medicationDetails'];
  imagingDetails?: Order['imagingDetails'];
  labDetails?: Order['labDetails'];
}

// -----------------------------------------------------------------------------
// Appointment
// -----------------------------------------------------------------------------

export interface Appointment {
  id: UUID;
  status: AppointmentStatus;
  appointmentType: AppointmentType;
  description?: string;
  start: DateTimeString;
  end: DateTimeString;
  minutesDuration: number;
  patient: Reference;
  provider: Reference;
  location?: Reference;
  reasonCode?: CodeableConcept[];
  comment?: string;
  patientInstruction?: string;
  cancelationReason?: string;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
}

export interface AppointmentCreateInput {
  appointmentType: AppointmentType;
  start: DateTimeString;
  end: DateTimeString;
  minutesDuration: number;
  patientId: UUID;
  providerId: UUID;
  locationId?: UUID;
  reasonCode?: CodeableConcept[];
  description?: string;
  comment?: string;
  patientInstruction?: string;
}

export interface AppointmentUpdateInput extends Partial<AppointmentCreateInput> {
  status?: AppointmentStatus;
  cancelationReason?: string;
}

export interface AppointmentSearchParams {
  date?: DateString;
  startDate?: DateString;
  endDate?: DateString;
  providerId?: UUID;
  patientId?: UUID;
  status?: AppointmentStatus;
  page?: number;
  pageSize?: number;
}

// -----------------------------------------------------------------------------
// User & Authentication
// -----------------------------------------------------------------------------

export interface User {
  id: UUID;
  email: string;
  firstName: string;
  lastName: string;
  role: UserRole;
  active: boolean;
  mfaEnabled: boolean;
  lastLogin?: DateTimeString;
  profilePhoto?: string;
  npi?: string;
  specialty?: string;
  department?: string;
  phone?: string;
  createdAt: DateTimeString;
  updatedAt: DateTimeString;
}

export interface LoginCredentials {
  email: string;
  password: string;
  mfaCode?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
}

export interface MFASetupResponse {
  secret: string;
  qrCodeUrl: string;
  backupCodes: string[];
}

// -----------------------------------------------------------------------------
// Audit Log
// -----------------------------------------------------------------------------

export interface AuditLog {
  id: UUID;
  timestamp: DateTimeString;
  userId: UUID;
  userName: string;
  action: AuditAction;
  resourceType: string;
  resourceId?: UUID;
  details?: string;
  ipAddress?: string;
  userAgent?: string;
  outcome: 'success' | 'failure';
}

// -----------------------------------------------------------------------------
// FHIR Resource (generic wrapper)
// -----------------------------------------------------------------------------

export interface FHIRResource<T = unknown> {
  resourceType: string;
  id: UUID;
  meta?: {
    versionId?: string;
    lastUpdated?: DateTimeString;
    source?: string;
    profile?: string[];
  };
  text?: {
    status: 'generated' | 'extensions' | 'additional' | 'empty';
    div: string;
  };
  resource: T;
}

export interface FHIRBundle<T = unknown> {
  resourceType: 'Bundle';
  type: 'searchset' | 'collection' | 'transaction' | 'batch';
  total: number;
  entry: Array<{
    fullUrl?: string;
    resource: FHIRResource<T>;
  }>;
  link?: Array<{
    relation: 'self' | 'next' | 'previous' | 'first' | 'last';
    url: string;
  }>;
}

// -----------------------------------------------------------------------------
// Notification
// -----------------------------------------------------------------------------

export interface Notification {
  id: UUID;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  read: boolean;
  actionUrl?: string;
  createdAt: DateTimeString;
}
