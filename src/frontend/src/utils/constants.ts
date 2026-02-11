import {
  UserRole,
  Gender,
  PatientStatus,
  EncounterStatus,
  EncounterClass,
  AppointmentStatus,
  AppointmentType,
  OrderType,
  OrderStatus,
  OrderPriority,
  MedicationRequestStatus,
  ConditionClinicalStatus,
  ObservationStatus,
} from '@/types';

// -----------------------------------------------------------------------------
// Application Constants
// -----------------------------------------------------------------------------

export const APP_NAME = 'OpenMedRecord';
export const APP_VERSION = '1.0.0';
export const APP_DESCRIPTION = 'Open Source Electronic Health Record System';

/** Session timeout in milliseconds (15 minutes) */
export const SESSION_TIMEOUT_MS = 15 * 60 * 1000;

/** Session warning before timeout in milliseconds (2 minutes before) */
export const SESSION_WARNING_MS = 2 * 60 * 1000;

/** Default page size for lists */
export const DEFAULT_PAGE_SIZE = 20;

/** Available page sizes */
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100] as const;

/** API base URL */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/** Token storage keys */
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'omr_access_token',
  REFRESH_TOKEN: 'omr_refresh_token',
  USER: 'omr_user',
  THEME: 'omr_theme',
  SIDEBAR_COLLAPSED: 'omr_sidebar_collapsed',
} as const;

// -----------------------------------------------------------------------------
// Label Maps
// -----------------------------------------------------------------------------

export const ROLE_LABELS: Record<UserRole, string> = {
  [UserRole.Admin]: 'Administrator',
  [UserRole.Physician]: 'Physician',
  [UserRole.Nurse]: 'Nurse',
  [UserRole.MedicalAssistant]: 'Medical Assistant',
  [UserRole.FrontDesk]: 'Front Desk',
  [UserRole.Billing]: 'Billing',
  [UserRole.LabTech]: 'Lab Technician',
  [UserRole.Pharmacist]: 'Pharmacist',
};

export const GENDER_LABELS: Record<Gender, string> = {
  [Gender.Male]: 'Male',
  [Gender.Female]: 'Female',
  [Gender.Other]: 'Other',
  [Gender.Unknown]: 'Unknown',
};

export const PATIENT_STATUS_LABELS: Record<PatientStatus, string> = {
  [PatientStatus.Active]: 'Active',
  [PatientStatus.Inactive]: 'Inactive',
  [PatientStatus.Deceased]: 'Deceased',
};

export const ENCOUNTER_STATUS_LABELS: Record<EncounterStatus, string> = {
  [EncounterStatus.Planned]: 'Planned',
  [EncounterStatus.InProgress]: 'In Progress',
  [EncounterStatus.OnLeave]: 'On Leave',
  [EncounterStatus.Finished]: 'Finished',
  [EncounterStatus.Cancelled]: 'Cancelled',
  [EncounterStatus.EnteredInError]: 'Entered in Error',
};

export const ENCOUNTER_CLASS_LABELS: Record<EncounterClass, string> = {
  [EncounterClass.Ambulatory]: 'Ambulatory',
  [EncounterClass.Emergency]: 'Emergency',
  [EncounterClass.Inpatient]: 'Inpatient',
  [EncounterClass.Observation]: 'Observation',
  [EncounterClass.Virtual]: 'Virtual',
};

export const APPOINTMENT_STATUS_LABELS: Record<AppointmentStatus, string> = {
  [AppointmentStatus.Proposed]: 'Proposed',
  [AppointmentStatus.Pending]: 'Pending',
  [AppointmentStatus.Booked]: 'Booked',
  [AppointmentStatus.Arrived]: 'Arrived',
  [AppointmentStatus.Fulfilled]: 'Fulfilled',
  [AppointmentStatus.Cancelled]: 'Cancelled',
  [AppointmentStatus.NoShow]: 'No Show',
  [AppointmentStatus.CheckedIn]: 'Checked In',
};

export const APPOINTMENT_TYPE_LABELS: Record<AppointmentType, string> = {
  [AppointmentType.Routine]: 'Routine',
  [AppointmentType.WalkIn]: 'Walk-In',
  [AppointmentType.Checkup]: 'Checkup',
  [AppointmentType.FollowUp]: 'Follow-Up',
  [AppointmentType.Emergency]: 'Emergency',
};

export const ORDER_TYPE_LABELS: Record<OrderType, string> = {
  [OrderType.Medication]: 'Medication',
  [OrderType.Laboratory]: 'Laboratory',
  [OrderType.Imaging]: 'Imaging',
  [OrderType.Procedure]: 'Procedure',
  [OrderType.Referral]: 'Referral',
};

export const ORDER_STATUS_LABELS: Record<OrderStatus, string> = {
  [OrderStatus.Draft]: 'Draft',
  [OrderStatus.Active]: 'Active',
  [OrderStatus.Completed]: 'Completed',
  [OrderStatus.Cancelled]: 'Cancelled',
  [OrderStatus.OnHold]: 'On Hold',
};

export const ORDER_PRIORITY_LABELS: Record<OrderPriority, string> = {
  [OrderPriority.Routine]: 'Routine',
  [OrderPriority.Urgent]: 'Urgent',
  [OrderPriority.ASAP]: 'ASAP',
  [OrderPriority.STAT]: 'STAT',
};

export const MEDICATION_STATUS_LABELS: Record<MedicationRequestStatus, string> = {
  [MedicationRequestStatus.Active]: 'Active',
  [MedicationRequestStatus.OnHold]: 'On Hold',
  [MedicationRequestStatus.Ended]: 'Ended',
  [MedicationRequestStatus.Stopped]: 'Stopped',
  [MedicationRequestStatus.Completed]: 'Completed',
  [MedicationRequestStatus.Cancelled]: 'Cancelled',
  [MedicationRequestStatus.EnteredInError]: 'Entered in Error',
  [MedicationRequestStatus.Draft]: 'Draft',
};

export const CONDITION_STATUS_LABELS: Record<ConditionClinicalStatus, string> = {
  [ConditionClinicalStatus.Active]: 'Active',
  [ConditionClinicalStatus.Recurrence]: 'Recurrence',
  [ConditionClinicalStatus.Relapse]: 'Relapse',
  [ConditionClinicalStatus.Inactive]: 'Inactive',
  [ConditionClinicalStatus.Remission]: 'Remission',
  [ConditionClinicalStatus.Resolved]: 'Resolved',
};

export const OBSERVATION_STATUS_LABELS: Record<ObservationStatus, string> = {
  [ObservationStatus.Registered]: 'Registered',
  [ObservationStatus.Preliminary]: 'Preliminary',
  [ObservationStatus.Final]: 'Final',
  [ObservationStatus.Amended]: 'Amended',
  [ObservationStatus.Corrected]: 'Corrected',
  [ObservationStatus.Cancelled]: 'Cancelled',
  [ObservationStatus.EnteredInError]: 'Entered in Error',
};

// -----------------------------------------------------------------------------
// Status Color Maps
// -----------------------------------------------------------------------------

export type StatusColor =
  | 'green'
  | 'yellow'
  | 'red'
  | 'blue'
  | 'gray'
  | 'purple'
  | 'orange'
  | 'teal';

export const ENCOUNTER_STATUS_COLORS: Record<EncounterStatus, StatusColor> = {
  [EncounterStatus.Planned]: 'blue',
  [EncounterStatus.InProgress]: 'green',
  [EncounterStatus.OnLeave]: 'yellow',
  [EncounterStatus.Finished]: 'gray',
  [EncounterStatus.Cancelled]: 'red',
  [EncounterStatus.EnteredInError]: 'red',
};

export const APPOINTMENT_STATUS_COLORS: Record<AppointmentStatus, StatusColor> = {
  [AppointmentStatus.Proposed]: 'purple',
  [AppointmentStatus.Pending]: 'yellow',
  [AppointmentStatus.Booked]: 'blue',
  [AppointmentStatus.Arrived]: 'teal',
  [AppointmentStatus.Fulfilled]: 'green',
  [AppointmentStatus.Cancelled]: 'red',
  [AppointmentStatus.NoShow]: 'red',
  [AppointmentStatus.CheckedIn]: 'green',
};

export const ORDER_STATUS_COLORS: Record<OrderStatus, StatusColor> = {
  [OrderStatus.Draft]: 'gray',
  [OrderStatus.Active]: 'blue',
  [OrderStatus.Completed]: 'green',
  [OrderStatus.Cancelled]: 'red',
  [OrderStatus.OnHold]: 'yellow',
};

export const ORDER_PRIORITY_COLORS: Record<OrderPriority, StatusColor> = {
  [OrderPriority.Routine]: 'gray',
  [OrderPriority.Urgent]: 'yellow',
  [OrderPriority.ASAP]: 'orange',
  [OrderPriority.STAT]: 'red',
};

// -----------------------------------------------------------------------------
// Select Options Helpers
// -----------------------------------------------------------------------------

export interface SelectOption<T = string> {
  value: T;
  label: string;
}

function mapToOptions<T extends string>(labels: Record<T, string>): SelectOption<T>[] {
  return Object.entries(labels).map(([value, label]) => ({
    value: value as T,
    label: label as string,
  }));
}

export const GENDER_OPTIONS = mapToOptions(GENDER_LABELS);
export const ENCOUNTER_STATUS_OPTIONS = mapToOptions(ENCOUNTER_STATUS_LABELS);
export const ENCOUNTER_CLASS_OPTIONS = mapToOptions(ENCOUNTER_CLASS_LABELS);
export const APPOINTMENT_STATUS_OPTIONS = mapToOptions(APPOINTMENT_STATUS_LABELS);
export const APPOINTMENT_TYPE_OPTIONS = mapToOptions(APPOINTMENT_TYPE_LABELS);
export const ORDER_TYPE_OPTIONS = mapToOptions(ORDER_TYPE_LABELS);
export const ORDER_STATUS_OPTIONS = mapToOptions(ORDER_STATUS_LABELS);
export const ORDER_PRIORITY_OPTIONS = mapToOptions(ORDER_PRIORITY_LABELS);
export const ROLE_OPTIONS = mapToOptions(ROLE_LABELS);

// US states for address forms
export const US_STATES: SelectOption[] = [
  { value: 'AL', label: 'Alabama' },
  { value: 'AK', label: 'Alaska' },
  { value: 'AZ', label: 'Arizona' },
  { value: 'AR', label: 'Arkansas' },
  { value: 'CA', label: 'California' },
  { value: 'CO', label: 'Colorado' },
  { value: 'CT', label: 'Connecticut' },
  { value: 'DE', label: 'Delaware' },
  { value: 'FL', label: 'Florida' },
  { value: 'GA', label: 'Georgia' },
  { value: 'HI', label: 'Hawaii' },
  { value: 'ID', label: 'Idaho' },
  { value: 'IL', label: 'Illinois' },
  { value: 'IN', label: 'Indiana' },
  { value: 'IA', label: 'Iowa' },
  { value: 'KS', label: 'Kansas' },
  { value: 'KY', label: 'Kentucky' },
  { value: 'LA', label: 'Louisiana' },
  { value: 'ME', label: 'Maine' },
  { value: 'MD', label: 'Maryland' },
  { value: 'MA', label: 'Massachusetts' },
  { value: 'MI', label: 'Michigan' },
  { value: 'MN', label: 'Minnesota' },
  { value: 'MS', label: 'Mississippi' },
  { value: 'MO', label: 'Missouri' },
  { value: 'MT', label: 'Montana' },
  { value: 'NE', label: 'Nebraska' },
  { value: 'NV', label: 'Nevada' },
  { value: 'NH', label: 'New Hampshire' },
  { value: 'NJ', label: 'New Jersey' },
  { value: 'NM', label: 'New Mexico' },
  { value: 'NY', label: 'New York' },
  { value: 'NC', label: 'North Carolina' },
  { value: 'ND', label: 'North Dakota' },
  { value: 'OH', label: 'Ohio' },
  { value: 'OK', label: 'Oklahoma' },
  { value: 'OR', label: 'Oregon' },
  { value: 'PA', label: 'Pennsylvania' },
  { value: 'RI', label: 'Rhode Island' },
  { value: 'SC', label: 'South Carolina' },
  { value: 'SD', label: 'South Dakota' },
  { value: 'TN', label: 'Tennessee' },
  { value: 'TX', label: 'Texas' },
  { value: 'UT', label: 'Utah' },
  { value: 'VT', label: 'Vermont' },
  { value: 'VA', label: 'Virginia' },
  { value: 'WA', label: 'Washington' },
  { value: 'WV', label: 'West Virginia' },
  { value: 'WI', label: 'Wisconsin' },
  { value: 'WY', label: 'Wyoming' },
  { value: 'DC', label: 'District of Columbia' },
];

// Marital status options
export const MARITAL_STATUS_OPTIONS: SelectOption[] = [
  { value: 'single', label: 'Single' },
  { value: 'married', label: 'Married' },
  { value: 'divorced', label: 'Divorced' },
  { value: 'widowed', label: 'Widowed' },
  { value: 'separated', label: 'Separated' },
  { value: 'domestic_partner', label: 'Domestic Partner' },
  { value: 'unknown', label: 'Unknown' },
];

// Language options
export const LANGUAGE_OPTIONS: SelectOption[] = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'zh', label: 'Chinese' },
  { value: 'ja', label: 'Japanese' },
  { value: 'ko', label: 'Korean' },
  { value: 'vi', label: 'Vietnamese' },
  { value: 'tl', label: 'Tagalog' },
  { value: 'ar', label: 'Arabic' },
  { value: 'hi', label: 'Hindi' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ru', label: 'Russian' },
  { value: 'other', label: 'Other' },
];

// Relationship options (for emergency contacts)
export const RELATIONSHIP_OPTIONS: SelectOption[] = [
  { value: 'spouse', label: 'Spouse' },
  { value: 'parent', label: 'Parent' },
  { value: 'child', label: 'Child' },
  { value: 'sibling', label: 'Sibling' },
  { value: 'friend', label: 'Friend' },
  { value: 'guardian', label: 'Guardian' },
  { value: 'other', label: 'Other' },
];

// Appointment duration options (in minutes)
export const APPOINTMENT_DURATION_OPTIONS: SelectOption<number>[] = [
  { value: 15, label: '15 minutes' },
  { value: 30, label: '30 minutes' },
  { value: 45, label: '45 minutes' },
  { value: 60, label: '1 hour' },
  { value: 90, label: '1.5 hours' },
  { value: 120, label: '2 hours' },
];
