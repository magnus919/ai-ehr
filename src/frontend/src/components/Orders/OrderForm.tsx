import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import {
  ExclamationTriangleIcon,
  ShieldExclamationIcon,
} from '@heroicons/react/24/outline';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { PatientSearch } from '@/components/Patients/PatientSearch';
import {
  ORDER_TYPE_OPTIONS,
  ORDER_PRIORITY_OPTIONS,
} from '@/utils/constants';
import type { DrugInteractionAlert, Patient, OrderType } from '@/types';

// -----------------------------------------------------------------------------
// Validation Schema
// -----------------------------------------------------------------------------

const orderFormSchema = z.object({
  type: z.string().min(1, 'Order type is required'),
  priority: z.string().min(1, 'Priority is required'),
  patientId: z.string().min(1, 'Patient is required'),
  patientDisplay: z.string().optional(),
  orderName: z.string().min(1, 'Order name is required'),
  orderCode: z.string().optional(),
  reason: z.string().optional(),
  note: z.string().optional(),

  // Medication-specific
  dosage: z.string().optional(),
  frequency: z.string().optional(),
  route: z.string().optional(),
  quantity: z.coerce.number().optional(),
  refills: z.coerce.number().min(0).max(12).optional(),
  pharmacy: z.string().optional(),

  // Lab-specific
  specimenType: z.string().optional(),
  fastingRequired: z.boolean().optional(),
  labInstructions: z.string().optional(),

  // Imaging-specific
  bodysite: z.string().optional(),
  contrast: z.boolean().optional(),
  imagingInstructions: z.string().optional(),
});

type OrderFormData = z.infer<typeof orderFormSchema>;

// -----------------------------------------------------------------------------
// Component Props
// -----------------------------------------------------------------------------

interface OrderFormProps {
  onSubmit: (data: OrderFormData) => void;
  isLoading?: boolean;
  onCancel?: () => void;
  /** Drug interaction alerts (would come from API check) */
  interactionAlerts?: DrugInteractionAlert[];
}

// -----------------------------------------------------------------------------
// OrderForm Component
// -----------------------------------------------------------------------------

export function OrderForm({
  onSubmit,
  isLoading = false,
  onCancel,
  interactionAlerts = [],
}: OrderFormProps) {
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<OrderFormData>({
    resolver: zodResolver(orderFormSchema),
    defaultValues: {
      type: '',
      priority: 'routine',
      patientId: '',
      fastingRequired: false,
      contrast: false,
      refills: 0,
    },
  });

  const orderType = watch('type') as OrderType | '';
  const patientDisplay = watch('patientDisplay');

  const handlePatientSelect = (patient: Patient) => {
    setValue('patientId', patient.id, { shouldValidate: true });
    setValue(
      'patientDisplay',
      `${patient.name.given?.[0] ?? ''} ${patient.name.family ?? ''} (MRN: ${patient.mrn})`,
    );
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6" noValidate>
      {/* Drug Interaction Alerts */}
      {interactionAlerts.length > 0 && (
        <div
          className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950/30"
          role="alert"
        >
          <div className="flex items-center gap-2">
            <ShieldExclamationIcon className="h-5 w-5 text-red-600" />
            <h3 className="text-sm font-semibold text-red-800 dark:text-red-200">
              Drug Interaction Alerts
            </h3>
          </div>
          <ul className="mt-2 space-y-2">
            {interactionAlerts.map((alert, i) => (
              <li key={i} className="flex items-start gap-2">
                <ExclamationTriangleIcon
                  className={`mt-0.5 h-4 w-4 flex-shrink-0 ${
                    alert.severity === 'high'
                      ? 'text-red-500'
                      : alert.severity === 'moderate'
                        ? 'text-yellow-500'
                        : 'text-blue-500'
                  }`}
                />
                <div>
                  <p className="text-sm font-medium text-red-800 dark:text-red-200">
                    {alert.severity.toUpperCase()}: Interaction with{' '}
                    {alert.interactingDrug}
                  </p>
                  <p className="text-xs text-red-600 dark:text-red-300">
                    {alert.description}
                  </p>
                  <p className="text-xs text-red-500 dark:text-red-400">
                    Recommendation: {alert.recommendation}
                  </p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Order Type and Priority */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="type" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Order Type <span className="text-red-500">*</span>
          </label>
          <select id="type" {...register('type')} className="input-base mt-1">
            <option value="">Select type</option>
            {ORDER_TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          {errors.type && (
            <p className="mt-1 text-sm text-red-600" role="alert">{errors.type.message}</p>
          )}
        </div>
        <div>
          <label htmlFor="priority" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Priority <span className="text-red-500">*</span>
          </label>
          <select id="priority" {...register('priority')} className="input-base mt-1">
            {ORDER_PRIORITY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Patient Selection */}
      <div>
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Patient <span className="text-red-500">*</span>
        </label>
        {patientDisplay ? (
          <div className="mt-1 flex items-center gap-2">
            <span className="input-base flex-1 bg-gray-50 dark:bg-gray-700">
              {patientDisplay}
            </span>
            <button
              type="button"
              onClick={() => {
                setValue('patientId', '');
                setValue('patientDisplay', '');
              }}
              className="btn-ghost text-xs"
            >
              Change
            </button>
          </div>
        ) : (
          <div className="mt-1">
            <PatientSearch onSelect={handlePatientSelect} showAutocomplete />
          </div>
        )}
        <input type="hidden" {...register('patientId')} />
        {errors.patientId && (
          <p className="mt-1 text-sm text-red-600" role="alert">{errors.patientId.message}</p>
        )}
      </div>

      {/* Order Name / Code */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <label htmlFor="orderName" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Order Name <span className="text-red-500">*</span>
          </label>
          <input
            id="orderName"
            {...register('orderName')}
            className="input-base mt-1"
            placeholder={
              orderType === 'medication'
                ? 'e.g., Amoxicillin 500mg capsule'
                : orderType === 'laboratory'
                  ? 'e.g., Complete Blood Count (CBC)'
                  : orderType === 'imaging'
                    ? 'e.g., Chest X-Ray PA/Lateral'
                    : 'Order name or description'
            }
          />
          {errors.orderName && (
            <p className="mt-1 text-sm text-red-600" role="alert">{errors.orderName.message}</p>
          )}
        </div>
      </div>

      {/* Medication-specific fields */}
      {orderType === 'medication' && (
        <fieldset className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <legend className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            Medication Details
          </legend>
          <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label htmlFor="dosage" className="block text-xs font-medium text-gray-500 dark:text-gray-400">Dosage</label>
              <input id="dosage" {...register('dosage')} className="input-base mt-1" placeholder="e.g., 500mg" />
            </div>
            <div>
              <label htmlFor="frequency" className="block text-xs font-medium text-gray-500 dark:text-gray-400">Frequency</label>
              <select id="frequency" {...register('frequency')} className="input-base mt-1">
                <option value="">Select</option>
                <option value="once_daily">Once daily</option>
                <option value="twice_daily">Twice daily (BID)</option>
                <option value="three_daily">Three times daily (TID)</option>
                <option value="four_daily">Four times daily (QID)</option>
                <option value="every_4h">Every 4 hours</option>
                <option value="every_6h">Every 6 hours</option>
                <option value="every_8h">Every 8 hours</option>
                <option value="as_needed">As needed (PRN)</option>
                <option value="at_bedtime">At bedtime (HS)</option>
              </select>
            </div>
            <div>
              <label htmlFor="route" className="block text-xs font-medium text-gray-500 dark:text-gray-400">Route</label>
              <select id="route" {...register('route')} className="input-base mt-1">
                <option value="">Select</option>
                <option value="oral">Oral (PO)</option>
                <option value="iv">Intravenous (IV)</option>
                <option value="im">Intramuscular (IM)</option>
                <option value="sc">Subcutaneous (SC)</option>
                <option value="topical">Topical</option>
                <option value="inhaled">Inhaled</option>
                <option value="rectal">Rectal</option>
                <option value="sublingual">Sublingual</option>
              </select>
            </div>
            <div>
              <label htmlFor="quantity" className="block text-xs font-medium text-gray-500 dark:text-gray-400">Quantity</label>
              <input id="quantity" type="number" {...register('quantity')} className="input-base mt-1" placeholder="30" />
            </div>
            <div>
              <label htmlFor="refills" className="block text-xs font-medium text-gray-500 dark:text-gray-400">Refills</label>
              <input id="refills" type="number" min="0" max="12" {...register('refills')} className="input-base mt-1" />
            </div>
            <div>
              <label htmlFor="pharmacy" className="block text-xs font-medium text-gray-500 dark:text-gray-400">Pharmacy</label>
              <input id="pharmacy" {...register('pharmacy')} className="input-base mt-1" placeholder="Preferred pharmacy" />
            </div>
          </div>
        </fieldset>
      )}

      {/* Lab-specific fields */}
      {orderType === 'laboratory' && (
        <fieldset className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <legend className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            Laboratory Details
          </legend>
          <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="specimenType" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
                Specimen Type
              </label>
              <select id="specimenType" {...register('specimenType')} className="input-base mt-1">
                <option value="">Select</option>
                <option value="blood">Blood</option>
                <option value="urine">Urine</option>
                <option value="stool">Stool</option>
                <option value="sputum">Sputum</option>
                <option value="csf">CSF</option>
                <option value="swab">Swab</option>
                <option value="tissue">Tissue</option>
              </select>
            </div>
            <div className="flex items-center gap-2 self-end">
              <input
                id="fastingRequired"
                type="checkbox"
                {...register('fastingRequired')}
                className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <label htmlFor="fastingRequired" className="text-sm text-gray-700 dark:text-gray-300">
                Fasting Required
              </label>
            </div>
            <div className="sm:col-span-2">
              <label htmlFor="labInstructions" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
                Special Instructions
              </label>
              <textarea id="labInstructions" rows={2} {...register('labInstructions')} className="input-base mt-1" />
            </div>
          </div>
        </fieldset>
      )}

      {/* Imaging-specific fields */}
      {orderType === 'imaging' && (
        <fieldset className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
          <legend className="text-sm font-semibold text-gray-700 dark:text-gray-300">
            Imaging Details
          </legend>
          <div className="mt-2 grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label htmlFor="bodysite" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
                Body Site
              </label>
              <input id="bodysite" {...register('bodysite')} className="input-base mt-1" placeholder="e.g., Chest, Left Knee" />
            </div>
            <div className="flex items-center gap-2 self-end">
              <input
                id="contrast"
                type="checkbox"
                {...register('contrast')}
                className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
              />
              <label htmlFor="contrast" className="text-sm text-gray-700 dark:text-gray-300">
                With Contrast
              </label>
            </div>
            <div className="sm:col-span-2">
              <label htmlFor="imagingInstructions" className="block text-xs font-medium text-gray-500 dark:text-gray-400">
                Clinical Indication / Instructions
              </label>
              <textarea id="imagingInstructions" rows={2} {...register('imagingInstructions')} className="input-base mt-1" />
            </div>
          </div>
        </fieldset>
      )}

      {/* Reason and Notes */}
      <div>
        <label htmlFor="reason" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Clinical Reason
        </label>
        <input id="reason" {...register('reason')} className="input-base mt-1" placeholder="Reason for the order" />
      </div>
      <div>
        <label htmlFor="note" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Additional Notes
        </label>
        <textarea id="note" rows={2} {...register('note')} className="input-base mt-1" />
      </div>

      {/* Form Actions */}
      <div className="flex items-center justify-end gap-3 border-t border-gray-200 pt-4 dark:border-gray-700">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary">
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={isLoading}
          className={
            interactionAlerts.some((a) => a.severity === 'high')
              ? 'btn-danger'
              : 'btn-primary'
          }
        >
          {isLoading ? (
            <LoadingSpinner size="sm" />
          ) : interactionAlerts.some((a) => a.severity === 'high') ? (
            'Submit with Override'
          ) : (
            'Submit Order'
          )}
        </button>
      </div>
    </form>
  );
}
