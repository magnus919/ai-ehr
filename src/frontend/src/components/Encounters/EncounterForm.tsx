import { useState, useCallback } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { PlusIcon, XMarkIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { useICD10Search } from '@/hooks/useEncounters';
import { ENCOUNTER_CLASS_OPTIONS } from '@/utils/constants';
import type { Encounter, EncounterClass } from '@/types';

// -----------------------------------------------------------------------------
// Validation Schema
// -----------------------------------------------------------------------------

const encounterFormSchema = z.object({
  encounterClass: z.string().min(1, 'Visit type is required'),
  chiefComplaint: z.string().min(1, 'Chief complaint is required').max(500),

  // Vital Signs
  temperature: z.coerce.number().min(80).max(120).optional().or(z.literal(0)),
  heartRate: z.coerce.number().min(20).max(300).optional().or(z.literal(0)),
  respiratoryRate: z.coerce.number().min(4).max(60).optional().or(z.literal(0)),
  bpSystolic: z.coerce.number().min(50).max(300).optional().or(z.literal(0)),
  bpDiastolic: z.coerce.number().min(20).max(200).optional().or(z.literal(0)),
  oxygenSaturation: z.coerce.number().min(50).max(100).optional().or(z.literal(0)),
  weight: z.coerce.number().min(0).max(1000).optional().or(z.literal(0)),
  height: z.coerce.number().min(0).max(300).optional().or(z.literal(0)),
  painLevel: z.coerce.number().min(0).max(10).optional().or(z.literal(0)),

  // SOAP Note
  subjective: z.string().optional(),
  objective: z.string().optional(),
  assessment: z.string().optional(),
  plan: z.string().optional(),

  notes: z.string().optional(),
});

type EncounterFormData = z.infer<typeof encounterFormSchema>;

// -----------------------------------------------------------------------------
// Component Props
// -----------------------------------------------------------------------------

interface EncounterFormProps {
  encounter?: Encounter;
  patientId: string;
  onSubmit: (data: EncounterFormData & { diagnoses: DiagnosisEntry[] }) => void;
  isLoading?: boolean;
  onCancel?: () => void;
}

interface DiagnosisEntry {
  code: string;
  display: string;
  rank: number;
}

// -----------------------------------------------------------------------------
// EncounterForm Component
// -----------------------------------------------------------------------------

export function EncounterForm({
  encounter,
  patientId,
  onSubmit,
  isLoading = false,
  onCancel,
}: EncounterFormProps) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<EncounterFormData>({
    resolver: zodResolver(encounterFormSchema),
    defaultValues: encounter
      ? {
          encounterClass: encounter.class,
          chiefComplaint: encounter.chiefComplaint ?? '',
          temperature: encounter.vitalSigns?.temperature ?? 0,
          heartRate: encounter.vitalSigns?.heartRate ?? 0,
          respiratoryRate: encounter.vitalSigns?.respiratoryRate ?? 0,
          bpSystolic: encounter.vitalSigns?.bloodPressureSystolic ?? 0,
          bpDiastolic: encounter.vitalSigns?.bloodPressureDiastolic ?? 0,
          oxygenSaturation: encounter.vitalSigns?.oxygenSaturation ?? 0,
          weight: encounter.vitalSigns?.weight ?? 0,
          height: encounter.vitalSigns?.height ?? 0,
          painLevel: encounter.vitalSigns?.painLevel ?? 0,
          subjective: encounter.soapNote?.subjective ?? '',
          objective: encounter.soapNote?.objective ?? '',
          assessment: encounter.soapNote?.assessment ?? '',
          plan: encounter.soapNote?.plan ?? '',
          notes: encounter.notes ?? '',
        }
      : {
          encounterClass: '',
          chiefComplaint: '',
        },
  });

  const [diagnoses, setDiagnoses] = useState<DiagnosisEntry[]>([]);
  const [icd10Query, setIcd10Query] = useState('');
  const [showICD10Search, setShowICD10Search] = useState(false);

  const { data: icd10Results, isLoading: icd10Loading } =
    useICD10Search(icd10Query);

  const addDiagnosis = useCallback(
    (code: string, display: string) => {
      if (diagnoses.some((d) => d.code === code)) return;
      setDiagnoses((prev) => [
        ...prev,
        { code, display, rank: prev.length + 1 },
      ]);
      setIcd10Query('');
      setShowICD10Search(false);
    },
    [diagnoses],
  );

  const removeDiagnosis = useCallback((code: string) => {
    setDiagnoses((prev) =>
      prev
        .filter((d) => d.code !== code)
        .map((d, i) => ({ ...d, rank: i + 1 })),
    );
  }, []);

  const handleFormSubmit = (data: EncounterFormData) => {
    onSubmit({ ...data, diagnoses });
  };

  return (
    <form
      onSubmit={handleSubmit(handleFormSubmit)}
      className="space-y-8"
      noValidate
    >
      {/* Visit Info */}
      <fieldset>
        <legend className="text-lg font-semibold text-gray-900 dark:text-white">
          Visit Information
        </legend>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label
              htmlFor="encounterClass"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Visit Type <span className="text-red-500">*</span>
            </label>
            <select
              id="encounterClass"
              {...register('encounterClass')}
              className="input-base mt-1"
            >
              <option value="">Select type</option>
              {ENCOUNTER_CLASS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            {errors.encounterClass && (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {errors.encounterClass.message}
              </p>
            )}
          </div>
          <div className="sm:col-span-2">
            <label
              htmlFor="chiefComplaint"
              className="block text-sm font-medium text-gray-700 dark:text-gray-300"
            >
              Chief Complaint <span className="text-red-500">*</span>
            </label>
            <input
              id="chiefComplaint"
              {...register('chiefComplaint')}
              className="input-base mt-1"
              placeholder="Reason for visit"
            />
            {errors.chiefComplaint && (
              <p className="mt-1 text-sm text-red-600" role="alert">
                {errors.chiefComplaint.message}
              </p>
            )}
          </div>
        </div>
      </fieldset>

      {/* Vital Signs */}
      <fieldset>
        <legend className="text-lg font-semibold text-gray-900 dark:text-white">
          Vital Signs
        </legend>
        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
          <div>
            <label htmlFor="temperature" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
              Temp (&deg;F)
            </label>
            <input id="temperature" type="number" step="0.1" {...register('temperature')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="heartRate" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
              HR (bpm)
            </label>
            <input id="heartRate" type="number" {...register('heartRate')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="respiratoryRate" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
              RR (breaths/min)
            </label>
            <input id="respiratoryRate" type="number" {...register('respiratoryRate')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="bpSystolic" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
              BP Systolic
            </label>
            <input id="bpSystolic" type="number" {...register('bpSystolic')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="bpDiastolic" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
              BP Diastolic
            </label>
            <input id="bpDiastolic" type="number" {...register('bpDiastolic')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="oxygenSaturation" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
              SpO2 (%)
            </label>
            <input id="oxygenSaturation" type="number" {...register('oxygenSaturation')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="weight" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
              Weight (lbs)
            </label>
            <input id="weight" type="number" step="0.1" {...register('weight')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="height" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
              Height (in)
            </label>
            <input id="height" type="number" step="0.1" {...register('height')} className="input-base mt-1" />
          </div>
          <div>
            <label htmlFor="painLevel" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
              Pain (0-10)
            </label>
            <input id="painLevel" type="number" min="0" max="10" {...register('painLevel')} className="input-base mt-1" />
          </div>
        </div>
      </fieldset>

      {/* SOAP Note */}
      <fieldset>
        <legend className="text-lg font-semibold text-gray-900 dark:text-white">
          SOAP Note
        </legend>
        <div className="mt-4 space-y-4">
          <div>
            <label htmlFor="subjective" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Subjective
            </label>
            <textarea
              id="subjective"
              rows={3}
              {...register('subjective')}
              className="input-base mt-1"
              placeholder="Patient's reported symptoms, history of present illness..."
            />
          </div>
          <div>
            <label htmlFor="objective" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Objective
            </label>
            <textarea
              id="objective"
              rows={3}
              {...register('objective')}
              className="input-base mt-1"
              placeholder="Physical exam findings, vital signs, test results..."
            />
          </div>
          <div>
            <label htmlFor="assessment" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Assessment
            </label>
            <textarea
              id="assessment"
              rows={3}
              {...register('assessment')}
              className="input-base mt-1"
              placeholder="Diagnoses and clinical impressions..."
            />
          </div>
          <div>
            <label htmlFor="plan" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Plan
            </label>
            <textarea
              id="plan"
              rows={3}
              {...register('plan')}
              className="input-base mt-1"
              placeholder="Treatment plan, orders, follow-up..."
            />
          </div>
        </div>
      </fieldset>

      {/* Diagnosis Entry (ICD-10 Search) */}
      <fieldset>
        <legend className="text-lg font-semibold text-gray-900 dark:text-white">
          Diagnoses
        </legend>

        {/* Current Diagnoses */}
        {diagnoses.length > 0 && (
          <div className="mt-4 space-y-2">
            {diagnoses.map((dx) => (
              <div
                key={dx.code}
                className="flex items-center justify-between rounded-md border border-gray-200 bg-gray-50 px-3 py-2 dark:border-gray-700 dark:bg-gray-800"
              >
                <div>
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {dx.display}
                  </span>
                  <span className="ml-2 font-mono text-xs text-gray-500">
                    {dx.code}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => removeDiagnosis(dx.code)}
                  className="rounded p-1 text-gray-400 hover:text-red-500"
                  aria-label={`Remove diagnosis ${dx.display}`}
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* ICD-10 Search */}
        <div className="relative mt-4">
          <div className="relative">
            <MagnifyingGlassIcon
              className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400"
              aria-hidden="true"
            />
            <input
              type="text"
              value={icd10Query}
              onChange={(e) => {
                setIcd10Query(e.target.value);
                setShowICD10Search(e.target.value.length >= 2);
              }}
              onFocus={() => {
                if (icd10Query.length >= 2) setShowICD10Search(true);
              }}
              placeholder="Search ICD-10 codes or descriptions..."
              className="input-base pl-9"
              aria-label="Search ICD-10 diagnosis codes"
            />
          </div>

          {showICD10Search && (
            <div className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded-md bg-white shadow-lg ring-1 ring-black/5 dark:bg-gray-800 dark:ring-gray-700">
              {icd10Loading ? (
                <div className="px-4 py-3">
                  <LoadingSpinner size="sm" />
                </div>
              ) : icd10Results?.length === 0 ? (
                <p className="px-4 py-3 text-sm text-gray-500">
                  No matching ICD-10 codes found.
                </p>
              ) : (
                icd10Results?.map((code) => (
                  <button
                    key={code.code}
                    type="button"
                    onClick={() => addDiagnosis(code.code, code.description)}
                    className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700"
                    disabled={diagnoses.some((d) => d.code === code.code)}
                  >
                    <span className="font-mono text-xs text-gray-400">
                      {code.code}
                    </span>
                    <span className="text-gray-900 dark:text-gray-100">
                      {code.description}
                    </span>
                  </button>
                ))
              )}
            </div>
          )}
        </div>
      </fieldset>

      {/* Additional Notes */}
      <div>
        <label
          htmlFor="notes"
          className="block text-sm font-medium text-gray-700 dark:text-gray-300"
        >
          Additional Notes
        </label>
        <textarea
          id="notes"
          rows={2}
          {...register('notes')}
          className="input-base mt-1"
          placeholder="Any additional clinical notes..."
        />
      </div>

      {/* Form Actions */}
      <div className="flex items-center justify-end gap-3 border-t border-gray-200 pt-6 dark:border-gray-700">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary">
            Cancel
          </button>
        )}
        <button type="submit" disabled={isLoading} className="btn-primary">
          {isLoading ? (
            <LoadingSpinner size="sm" />
          ) : encounter ? (
            'Update Encounter'
          ) : (
            'Create Encounter'
          )}
        </button>
      </div>
    </form>
  );
}
