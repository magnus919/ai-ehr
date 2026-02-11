import {
  format,
  formatDistanceToNow,
  parseISO,
  isValid,
  differenceInYears,
} from 'date-fns';
import type { HumanName, Patient } from '@/types';

// -----------------------------------------------------------------------------
// Date Formatters
// -----------------------------------------------------------------------------

/**
 * Format a date string to a display format.
 * @example formatDate('2024-03-15') => 'Mar 15, 2024'
 */
export function formatDate(date: string | Date | null | undefined, pattern = 'MMM d, yyyy'): string {
  if (!date) return '--';
  const parsed = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(parsed)) return '--';
  return format(parsed, pattern);
}

/**
 * Format a datetime string to include time.
 * @example formatDateTime('2024-03-15T14:30:00Z') => 'Mar 15, 2024 2:30 PM'
 */
export function formatDateTime(
  date: string | Date | null | undefined,
  pattern = 'MMM d, yyyy h:mm a',
): string {
  if (!date) return '--';
  const parsed = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(parsed)) return '--';
  return format(parsed, pattern);
}

/**
 * Format a time string.
 * @example formatTime('2024-03-15T14:30:00Z') => '2:30 PM'
 */
export function formatTime(
  date: string | Date | null | undefined,
  pattern = 'h:mm a',
): string {
  if (!date) return '--';
  const parsed = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(parsed)) return '--';
  return format(parsed, pattern);
}

/**
 * Format a date as a relative time string.
 * @example formatRelativeTime('2024-03-15T14:30:00Z') => '2 hours ago'
 */
export function formatRelativeTime(date: string | Date | null | undefined): string {
  if (!date) return '--';
  const parsed = typeof date === 'string' ? parseISO(date) : date;
  if (!isValid(parsed)) return '--';
  return formatDistanceToNow(parsed, { addSuffix: true });
}

/**
 * Calculate age from birth date.
 * @example calculateAge('1990-05-20') => 34
 */
export function calculateAge(birthDate: string | Date | null | undefined): number | null {
  if (!birthDate) return null;
  const parsed = typeof birthDate === 'string' ? parseISO(birthDate) : birthDate;
  if (!isValid(parsed)) return null;
  return differenceInYears(new Date(), parsed);
}

/**
 * Format a date of birth with age.
 * @example formatDOBWithAge('1990-05-20') => 'May 20, 1990 (34 yo)'
 */
export function formatDOBWithAge(birthDate: string | null | undefined): string {
  if (!birthDate) return '--';
  const age = calculateAge(birthDate);
  const formatted = formatDate(birthDate);
  if (age === null) return formatted;
  return `${formatted} (${age} yo)`;
}

// -----------------------------------------------------------------------------
// Name Formatters
// -----------------------------------------------------------------------------

/**
 * Format a HumanName to display format.
 * @example formatName({ family: 'Smith', given: ['John', 'A'] }) => 'John A Smith'
 */
export function formatName(name: HumanName | null | undefined): string {
  if (!name) return '--';
  const parts: string[] = [];
  if (name.prefix?.length) parts.push(name.prefix.join(' '));
  if (name.given?.length) parts.push(name.given.join(' '));
  if (name.family) parts.push(name.family);
  if (name.suffix?.length) parts.push(name.suffix.join(' '));
  return parts.join(' ') || '--';
}

/**
 * Format a name as "Last, First".
 * @example formatNameLastFirst({ family: 'Smith', given: ['John'] }) => 'Smith, John'
 */
export function formatNameLastFirst(name: HumanName | null | undefined): string {
  if (!name) return '--';
  const parts: string[] = [];
  if (name.family) parts.push(name.family);
  if (name.given?.length) {
    if (parts.length > 0) parts.push(', ');
    parts.push(name.given.join(' '));
  }
  return parts.join('') || '--';
}

/**
 * Get initials from a HumanName.
 * @example getInitials({ family: 'Smith', given: ['John'] }) => 'JS'
 */
export function getInitials(name: HumanName | null | undefined): string {
  if (!name) return '??';
  const firstInitial = name.given?.[0]?.charAt(0)?.toUpperCase() ?? '?';
  const lastInitial = name.family?.charAt(0)?.toUpperCase() ?? '?';
  return `${firstInitial}${lastInitial}`;
}

/**
 * Format a patient's full display string.
 * @example formatPatientDisplay(patient) => 'Smith, John (MRN: 12345) - M, 34 yo'
 */
export function formatPatientDisplay(patient: Patient | null | undefined): string {
  if (!patient) return '--';
  const name = formatNameLastFirst(patient.name);
  const age = calculateAge(patient.birthDate);
  const gender = patient.gender?.charAt(0)?.toUpperCase() ?? '?';
  const agePart = age !== null ? `, ${age} yo` : '';
  return `${name} (MRN: ${patient.mrn}) - ${gender}${agePart}`;
}

// -----------------------------------------------------------------------------
// Phone / Contact Formatters
// -----------------------------------------------------------------------------

/**
 * Format a phone number.
 * @example formatPhone('5551234567') => '(555) 123-4567'
 */
export function formatPhone(phone: string | null | undefined): string {
  if (!phone) return '--';
  const cleaned = phone.replace(/\D/g, '');
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  if (cleaned.length === 11 && cleaned.startsWith('1')) {
    return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
  }
  return phone;
}

// -----------------------------------------------------------------------------
// SSN Formatter
// -----------------------------------------------------------------------------

/**
 * Mask an SSN, showing only last 4 digits.
 * @example formatSSN('123456789') => '***-**-6789'
 */
export function formatSSN(ssn: string | null | undefined): string {
  if (!ssn) return '--';
  const cleaned = ssn.replace(/\D/g, '');
  if (cleaned.length !== 9) return '***-**-****';
  return `***-**-${cleaned.slice(5)}`;
}

/**
 * Format full SSN (for authorized views only).
 * @example formatSSNFull('123456789') => '123-45-6789'
 */
export function formatSSNFull(ssn: string | null | undefined): string {
  if (!ssn) return '--';
  const cleaned = ssn.replace(/\D/g, '');
  if (cleaned.length !== 9) return ssn;
  return `${cleaned.slice(0, 3)}-${cleaned.slice(3, 5)}-${cleaned.slice(5)}`;
}

// -----------------------------------------------------------------------------
// MRN Formatter
// -----------------------------------------------------------------------------

/**
 * Format MRN with leading zeros.
 * @example formatMRN('12345') => 'MRN-0012345'
 */
export function formatMRN(mrn: string | null | undefined): string {
  if (!mrn) return '--';
  return mrn.startsWith('MRN') ? mrn : `MRN-${mrn.padStart(7, '0')}`;
}

// -----------------------------------------------------------------------------
// Clinical Formatters
// -----------------------------------------------------------------------------

/**
 * Format a blood pressure reading.
 * @example formatBloodPressure(120, 80) => '120/80 mmHg'
 */
export function formatBloodPressure(
  systolic: number | null | undefined,
  diastolic: number | null | undefined,
): string {
  if (systolic == null || diastolic == null) return '--';
  return `${systolic}/${diastolic} mmHg`;
}

/**
 * Format a temperature.
 * @example formatTemperature(98.6, 'F') => '98.6 °F'
 */
export function formatTemperature(
  value: number | null | undefined,
  unit: 'F' | 'C' = 'F',
): string {
  if (value == null) return '--';
  return `${value.toFixed(1)} °${unit}`;
}

/**
 * Format a weight value.
 */
export function formatWeight(
  value: number | null | undefined,
  unit: 'kg' | 'lb' = 'lb',
): string {
  if (value == null) return '--';
  return `${value.toFixed(1)} ${unit}`;
}

/**
 * Format a height value.
 */
export function formatHeight(
  value: number | null | undefined,
  unit: 'cm' | 'in' = 'in',
): string {
  if (value == null) return '--';
  if (unit === 'in') {
    const feet = Math.floor(value / 12);
    const inches = Math.round(value % 12);
    return `${feet}'${inches}"`;
  }
  return `${value.toFixed(0)} cm`;
}

// -----------------------------------------------------------------------------
// General Formatters
// -----------------------------------------------------------------------------

/**
 * Capitalize the first letter of a string.
 */
export function capitalize(str: string | null | undefined): string {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Convert an enum-like string to a display label.
 * @example enumToLabel('in-progress') => 'In Progress'
 */
export function enumToLabel(value: string | null | undefined): string {
  if (!value) return '--';
  return value
    .replace(/[_-]/g, ' ')
    .replace(/\b\w/g, (l) => l.toUpperCase());
}

/**
 * Truncate a string to a given length with ellipsis.
 */
export function truncate(str: string | null | undefined, maxLength: number): string {
  if (!str) return '';
  if (str.length <= maxLength) return str;
  return `${str.slice(0, maxLength)}...`;
}

/**
 * Format a number as currency.
 */
export function formatCurrency(value: number | null | undefined): string {
  if (value == null) return '--';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
}
