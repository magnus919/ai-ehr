import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import {
  GENDER_OPTIONS,
  MARITAL_STATUS_OPTIONS,
  LANGUAGE_OPTIONS,
  US_STATES,
  RELATIONSHIP_OPTIONS,
} from '@/utils/constants';
import type { Patient } from '@/types';

// -----------------------------------------------------------------------------
// Validation Schema
// -----------------------------------------------------------------------------

const patientFormSchema = z.object({
  firstName: z.string().min(1, 'First name is required').max(100),
  lastName: z.string().min(1, 'Last name is required').max(100),
  middleName: z.string().max(100).optional(),
  prefix: z.string().max(20).optional(),
  suffix: z.string().max(20).optional(),
  gender: z.enum(['male', 'female', 'other', 'unknown'], {
    required_error: 'Gender is required',
  }),
  birthDate: z.string().min(1, 'Date of birth is required'),
  ssn: z
    .string()
    .regex(/^\d{3}-?\d{2}-?\d{4}$/, 'Invalid SSN format')
    .optional()
    .or(z.literal('')),
  maritalStatus: z.string().optional(),
  language: z.string().optional(),
  race: z.string().optional(),
  ethnicity: z.string().optional(),

  // Contact info
  phone: z.string().optional(),
  email: z.string().email('Invalid email').optional().or(z.literal('')),

  // Address
  addressLine1: z.string().optional(),
  addressLine2: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  postalCode: z
    .string()
    .regex(/^\d{5}(-\d{4})?$/, 'Invalid zip code')
    .optional()
    .or(z.literal('')),
  country: z.string().default('US'),

  // Insurance
  insuranceProvider: z.string().optional(),
  insurancePlan: z.string().optional(),
  insuranceMemberId: z.string().optional(),
  insuranceGroupNumber: z.string().optional(),

  // Emergency Contacts
  emergencyContacts: z
    .array(
      z.object({
        name: z.string().min(1, 'Name is required'),
        relationship: z.string().min(1, 'Relationship is required'),
        phone: z.string().min(1, 'Phone is required'),
        email: z.string().email('Invalid email').optional().or(z.literal('')),
      }),
    )
    .optional(),
});

type PatientFormData = z.infer<typeof patientFormSchema>;

// -----------------------------------------------------------------------------
// Component Props
// -----------------------------------------------------------------------------

interface PatientFormProps {
  /** Existing patient data for editing */
  patient?: Patient;
  /** Called on form submission */
  onSubmit: (data: PatientFormData) => void;
  /** Loading state */
  isLoading?: boolean;
  /** Called when cancel is clicked */
  onCancel?: () => void;
}

// -----------------------------------------------------------------------------
// PatientForm Component
// -----------------------------------------------------------------------------

export function PatientForm({
  patient,
  onSubmit,
  isLoading = false,
  onCancel,
}: PatientFormProps) {
  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isDirty },
  } = useForm<PatientFormData>({
    resolver: zodResolver(patientFormSchema),
    defaultValues: patient
      ? {
          firstName: patient.name.given?.[0] ?? '',
          middleName: patient.name.given?.[1] ?? '',
          lastName: patient.name.family ?? '',
          prefix: patient.name.prefix?.[0] ?? '',
          suffix: patient.name.suffix?.[0] ?? '',
          gender: patient.gender,
          birthDate: patient.birthDate,
          ssn: patient.ssn ?? '',
          maritalStatus: patient.maritalStatus ?? '',
          language: patient.language ?? '',
          race: patient.race ?? '',
          ethnicity: patient.ethnicity ?? '',
          phone:
            patient.telecom?.find((t) => t.system === 'phone')?.value ?? '',
          email:
            patient.telecom?.find((t) => t.system === 'email')?.value ?? '',
          addressLine1: patient.address?.[0]?.line1 ?? '',
          addressLine2: patient.address?.[0]?.line2 ?? '',
          city: patient.address?.[0]?.city ?? '',
          state: patient.address?.[0]?.state ?? '',
          postalCode: patient.address?.[0]?.postalCode ?? '',
          country: patient.address?.[0]?.country ?? 'US',
          insuranceProvider: patient.insurance?.[0]?.provider ?? '',
          insurancePlan: patient.insurance?.[0]?.planName ?? '',
          insuranceMemberId: patient.insurance?.[0]?.memberId ?? '',
          insuranceGroupNumber: patient.insurance?.[0]?.groupNumber ?? '',
          emergencyContacts: patient.emergencyContacts ?? [],
        }
      : {
          gender: undefined,
          country: 'US',
          emergencyContacts: [],
        },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'emergencyContacts',
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-8" noValidate>
      {/* Demographics Section */}
      <fieldset>
        <legend className="text-lg font-semibold text-gray-900 dark:text-white">
          Demographics
        </legend>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Basic patient identification information.
        </p>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="sm:col-span-1">
            <label htmlFor="prefix" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Prefix
            </label>
            <input id="prefix" {...register('prefix')} className="input-base mt-1" placeholder="Dr., Mr., Ms." />
          </div>
          <div>
            <label htmlFor="firstName" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              First Name <span className="text-red-500">*</span>
            </label>
            <input
              id="firstName"
              {...register('firstName')}
              className="input-base mt-1"
              aria-invalid={!!errors.firstName}
              aria-describedby={errors.firstName ? 'firstName-error' : undefined}
            />
            {errors.firstName && (
              <p id="firstName-error" className="mt-1 text-sm text-red-600" role="alert">
                {errors.firstName.message}
              </p>
            )}
          </div>
          <div>
            <label htmlFor="middleName" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Middle Name
            </label>
            <input id="middleName" {...register('middleName')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="lastName" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Last Name <span className="text-red-500">*</span>
            </label>
            <input
              id="lastName"
              {...register('lastName')}
              className="input-base mt-1"
              aria-invalid={!!errors.lastName}
              aria-describedby={errors.lastName ? 'lastName-error' : undefined}
            />
            {errors.lastName && (
              <p id="lastName-error" className="mt-1 text-sm text-red-600" role="alert">
                {errors.lastName.message}
              </p>
            )}
          </div>
          <div>
            <label htmlFor="suffix" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Suffix
            </label>
            <input id="suffix" {...register('suffix')} className="input-base mt-1" placeholder="Jr., Sr., III" />
          </div>
          <div>
            <label htmlFor="gender" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Gender <span className="text-red-500">*</span>
            </label>
            <select
              id="gender"
              {...register('gender')}
              className="input-base mt-1"
              aria-invalid={!!errors.gender}
            >
              <option value="">Select gender</option>
              {GENDER_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            {errors.gender && (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {errors.gender.message}
              </p>
            )}
          </div>
          <div>
            <label htmlFor="birthDate" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Date of Birth <span className="text-red-500">*</span>
            </label>
            <input
              id="birthDate"
              type="date"
              {...register('birthDate')}
              className="input-base mt-1"
              max={new Date().toISOString().split('T')[0]}
              aria-invalid={!!errors.birthDate}
            />
            {errors.birthDate && (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {errors.birthDate.message}
              </p>
            )}
          </div>
          <div>
            <label htmlFor="ssn" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              SSN
            </label>
            <input
              id="ssn"
              {...register('ssn')}
              className="input-base mt-1"
              placeholder="XXX-XX-XXXX"
              maxLength={11}
            />
            {errors.ssn && (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {errors.ssn.message}
              </p>
            )}
          </div>
          <div>
            <label htmlFor="maritalStatus" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Marital Status
            </label>
            <select id="maritalStatus" {...register('maritalStatus')} className="input-base mt-1">
              <option value="">Select</option>
              {MARITAL_STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="language" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Preferred Language
            </label>
            <select id="language" {...register('language')} className="input-base mt-1">
              <option value="">Select</option>
              {LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>
      </fieldset>

      {/* Contact Information */}
      <fieldset>
        <legend className="text-lg font-semibold text-gray-900 dark:text-white">
          Contact Information
        </legend>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Phone Number
            </label>
            <input id="phone" type="tel" {...register('phone')} className="input-base mt-1" placeholder="(555) 123-4567" />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Email
            </label>
            <input
              id="email"
              type="email"
              {...register('email')}
              className="input-base mt-1"
              placeholder="patient@example.com"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600" role="alert">{errors.email.message}</p>
            )}
          </div>
        </div>
      </fieldset>

      {/* Address */}
      <fieldset>
        <legend className="text-lg font-semibold text-gray-900 dark:text-white">
          Address
        </legend>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="sm:col-span-2 lg:col-span-3">
            <label htmlFor="addressLine1" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Street Address
            </label>
            <input id="addressLine1" {...register('addressLine1')} className="input-base mt-1" />
          </div>
          <div className="sm:col-span-2 lg:col-span-3">
            <label htmlFor="addressLine2" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Apt / Suite / Unit
            </label>
            <input id="addressLine2" {...register('addressLine2')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="city" className="block text-sm font-medium text-gray-700 dark:text-gray-300">City</label>
            <input id="city" {...register('city')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="state" className="block text-sm font-medium text-gray-700 dark:text-gray-300">State</label>
            <select id="state" {...register('state')} className="input-base mt-1">
              <option value="">Select state</option>
              {US_STATES.map((s) => (
                <option key={s.value} value={s.value}>{s.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="postalCode" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              ZIP Code
            </label>
            <input id="postalCode" {...register('postalCode')} className="input-base mt-1" placeholder="12345" />
            {errors.postalCode && (
              <p className="mt-1 text-sm text-red-600" role="alert">{errors.postalCode.message}</p>
            )}
          </div>
        </div>
      </fieldset>

      {/* Insurance */}
      <fieldset>
        <legend className="text-lg font-semibold text-gray-900 dark:text-white">
          Insurance
        </legend>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="insuranceProvider" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Insurance Provider
            </label>
            <input id="insuranceProvider" {...register('insuranceProvider')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="insurancePlan" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Plan Name
            </label>
            <input id="insurancePlan" {...register('insurancePlan')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="insuranceMemberId" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Member ID
            </label>
            <input id="insuranceMemberId" {...register('insuranceMemberId')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="insuranceGroupNumber" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Group Number
            </label>
            <input id="insuranceGroupNumber" {...register('insuranceGroupNumber')} className="input-base mt-1" />
          </div>
        </div>
      </fieldset>

      {/* Emergency Contacts */}
      <fieldset>
        <legend className="text-lg font-semibold text-gray-900 dark:text-white">
          Emergency Contacts
        </legend>
        <div className="mt-4 space-y-4">
          {fields.map((field, index) => (
            <div
              key={field.id}
              className="grid grid-cols-1 gap-4 rounded-lg border border-gray-200 p-4 dark:border-gray-700 sm:grid-cols-2 lg:grid-cols-4"
            >
              <div>
                <label
                  htmlFor={`emergencyContacts.${index}.name`}
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Name <span className="text-red-500">*</span>
                </label>
                <input
                  id={`emergencyContacts.${index}.name`}
                  {...register(`emergencyContacts.${index}.name`)}
                  className="input-base mt-1"
                />
                {errors.emergencyContacts?.[index]?.name && (
                  <p className="mt-1 text-sm text-red-600" role="alert">
                    {errors.emergencyContacts[index]?.name?.message}
                  </p>
                )}
              </div>
              <div>
                <label
                  htmlFor={`emergencyContacts.${index}.relationship`}
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Relationship <span className="text-red-500">*</span>
                </label>
                <select
                  id={`emergencyContacts.${index}.relationship`}
                  {...register(`emergencyContacts.${index}.relationship`)}
                  className="input-base mt-1"
                >
                  <option value="">Select</option>
                  {RELATIONSHIP_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label
                  htmlFor={`emergencyContacts.${index}.phone`}
                  className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                >
                  Phone <span className="text-red-500">*</span>
                </label>
                <input
                  id={`emergencyContacts.${index}.phone`}
                  type="tel"
                  {...register(`emergencyContacts.${index}.phone`)}
                  className="input-base mt-1"
                />
              </div>
              <div className="flex items-end gap-2">
                <div className="flex-1">
                  <label
                    htmlFor={`emergencyContacts.${index}.email`}
                    className="block text-sm font-medium text-gray-700 dark:text-gray-300"
                  >
                    Email
                  </label>
                  <input
                    id={`emergencyContacts.${index}.email`}
                    type="email"
                    {...register(`emergencyContacts.${index}.email`)}
                    className="input-base mt-1"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => remove(index)}
                  className="mb-1 rounded-md p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30"
                  aria-label={`Remove emergency contact ${index + 1}`}
                >
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          ))}
          <button
            type="button"
            onClick={() =>
              append({ name: '', relationship: '', phone: '', email: '' })
            }
            className="btn-secondary"
          >
            <PlusIcon className="h-4 w-4" />
            Add Emergency Contact
          </button>
        </div>
      </fieldset>

      {/* Form Actions */}
      <div className="flex items-center justify-end gap-3 border-t border-gray-200 pt-6 dark:border-gray-700">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary">
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isLoading || (!isDirty && !!patient)}
          className="btn-primary"
        >
          {isLoading ? (
            <LoadingSpinner size="sm" />
          ) : patient ? (
            'Update Patient'
          ) : (
            'Register Patient'
          )}
        </button>
      </div>
    </form>
  );
}
