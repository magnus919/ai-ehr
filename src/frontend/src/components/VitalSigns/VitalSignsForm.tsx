import { useState, useEffect } from 'react';
import { useCreateObservation } from '@/hooks/useObservations';
import type { ObservationCreate } from '@/services/observations';

interface VitalSignsFormProps {
  patientId: string;
  encounterId?: string;
  onSuccess?: () => void;
}

const LOINC_CODES = {
  heartRate: { code: '8867-4', display: 'Heart rate', unit: 'beats/min' },
  systolicBP: { code: '8480-6', display: 'Systolic blood pressure', unit: 'mmHg' },
  diastolicBP: { code: '8462-4', display: 'Diastolic blood pressure', unit: 'mmHg' },
  temperature: { code: '8310-5', display: 'Body temperature', unit: 'F' },
  respiratoryRate: { code: '9279-1', display: 'Respiratory rate', unit: 'breaths/min' },
  spo2: { code: '2708-6', display: 'Oxygen saturation', unit: '%' },
  height: { code: '8302-2', display: 'Body height', unit: 'cm' },
  weight: { code: '29463-7', display: 'Body weight', unit: 'kg' },
  bmi: { code: '39156-5', display: 'Body mass index', unit: 'kg/m2' },
};

const NORMAL_RANGES = {
  heartRate: { min: 60, max: 100, critical: { min: 40, max: 140 } },
  systolicBP: { min: 90, max: 120, critical: { min: 70, max: 180 } },
  diastolicBP: { min: 60, max: 80, critical: { min: 40, max: 110 } },
  temperature: { min: 97.0, max: 99.0, critical: { min: 95.0, max: 103.0 } },
  respiratoryRate: { min: 12, max: 20, critical: { min: 8, max: 30 } },
  spo2: { min: 95, max: 100, critical: { min: 90, max: 100 } },
};

type VitalStatus = 'normal' | 'warning' | 'critical';

function getVitalStatus(
  value: number | undefined,
  vitalType: keyof typeof NORMAL_RANGES
): VitalStatus {
  if (!value) return 'normal';
  const range = NORMAL_RANGES[vitalType];
  if (value < range.critical.min || value > range.critical.max) return 'critical';
  if (value < range.min || value > range.max) return 'warning';
  return 'normal';
}

function getStatusColor(status: VitalStatus): string {
  switch (status) {
    case 'critical':
      return 'border-red-500 bg-red-50 dark:bg-red-950/20';
    case 'warning':
      return 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20';
    default:
      return 'border-gray-300 dark:border-gray-600';
  }
}

export function VitalSignsForm({ patientId, encounterId, onSuccess }: VitalSignsFormProps) {
  const [vitals, setVitals] = useState({
    heartRate: '',
    systolicBP: '',
    diastolicBP: '',
    temperature: '',
    respiratoryRate: '',
    spo2: '',
    height: '',
    weight: '',
  });

  const [bmi, setBmi] = useState<number | null>(null);
  const createObservation = useCreateObservation();

  useEffect(() => {
    const height = parseFloat(vitals.height);
    const weight = parseFloat(vitals.weight);
    if (height > 0 && weight > 0) {
      const heightInMeters = height / 100;
      const calculatedBmi = weight / (heightInMeters * heightInMeters);
      setBmi(parseFloat(calculatedBmi.toFixed(1)));
    } else {
      setBmi(null);
    }
  }, [vitals.height, vitals.weight]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const observations: ObservationCreate[] = [];
    const effectiveDate = new Date().toISOString();

    const addObservation = (
      vitalKey: keyof typeof vitals,
      loincKey: keyof typeof LOINC_CODES
    ) => {
      const value = vitals[vitalKey];
      if (value) {
        const loinc = LOINC_CODES[loincKey];
        observations.push({
          patient_id: patientId,
          encounter_id: encounterId,
          code: loinc.code,
          code_system: 'http://loinc.org',
          display: loinc.display,
          value_type: 'Quantity',
          value_numeric: parseFloat(value),
          unit: loinc.unit,
          effective_date: effectiveDate,
          status: 'final',
        });
      }
    };

    addObservation('heartRate', 'heartRate');
    addObservation('systolicBP', 'systolicBP');
    addObservation('diastolicBP', 'diastolicBP');
    addObservation('temperature', 'temperature');
    addObservation('respiratoryRate', 'respiratoryRate');
    addObservation('spo2', 'spo2');
    addObservation('height', 'height');
    addObservation('weight', 'weight');

    if (bmi !== null) {
      observations.push({
        patient_id: patientId,
        encounter_id: encounterId,
        code: LOINC_CODES.bmi.code,
        code_system: 'http://loinc.org',
        display: LOINC_CODES.bmi.display,
        value_type: 'Quantity',
        value_numeric: bmi,
        unit: LOINC_CODES.bmi.unit,
        effective_date: effectiveDate,
        status: 'final',
      });
    }

    for (const obs of observations) {
      await createObservation.mutateAsync(obs);
    }

    setVitals({
      heartRate: '',
      systolicBP: '',
      diastolicBP: '',
      temperature: '',
      respiratoryRate: '',
      spo2: '',
      height: '',
      weight: '',
    });

    if (onSuccess) onSuccess();
  };

  const handleChange = (field: keyof typeof vitals, value: string) => {
    setVitals((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="card space-y-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
        Record Vital Signs
      </h2>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Heart Rate (bpm)
          </label>
          <input
            type="number"
            step="1"
            value={vitals.heartRate}
            onChange={(e) => handleChange('heartRate', e.target.value)}
            className={`input-base mt-1 ${getStatusColor(
              getVitalStatus(parseFloat(vitals.heartRate), 'heartRate')
            )}`}
            placeholder="60-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Systolic BP (mmHg)
          </label>
          <input
            type="number"
            step="1"
            value={vitals.systolicBP}
            onChange={(e) => handleChange('systolicBP', e.target.value)}
            className={`input-base mt-1 ${getStatusColor(
              getVitalStatus(parseFloat(vitals.systolicBP), 'systolicBP')
            )}`}
            placeholder="90-120"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Diastolic BP (mmHg)
          </label>
          <input
            type="number"
            step="1"
            value={vitals.diastolicBP}
            onChange={(e) => handleChange('diastolicBP', e.target.value)}
            className={`input-base mt-1 ${getStatusColor(
              getVitalStatus(parseFloat(vitals.diastolicBP), 'diastolicBP')
            )}`}
            placeholder="60-80"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Temperature (°F)
          </label>
          <input
            type="number"
            step="0.1"
            value={vitals.temperature}
            onChange={(e) => handleChange('temperature', e.target.value)}
            className={`input-base mt-1 ${getStatusColor(
              getVitalStatus(parseFloat(vitals.temperature), 'temperature')
            )}`}
            placeholder="97.0-99.0"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Respiratory Rate (breaths/min)
          </label>
          <input
            type="number"
            step="1"
            value={vitals.respiratoryRate}
            onChange={(e) => handleChange('respiratoryRate', e.target.value)}
            className={`input-base mt-1 ${getStatusColor(
              getVitalStatus(parseFloat(vitals.respiratoryRate), 'respiratoryRate')
            )}`}
            placeholder="12-20"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            SpO2 (%)
          </label>
          <input
            type="number"
            step="1"
            value={vitals.spo2}
            onChange={(e) => handleChange('spo2', e.target.value)}
            className={`input-base mt-1 ${getStatusColor(
              getVitalStatus(parseFloat(vitals.spo2), 'spo2')
            )}`}
            placeholder="95-100"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Height (cm)
          </label>
          <input
            type="number"
            step="0.1"
            value={vitals.height}
            onChange={(e) => handleChange('height', e.target.value)}
            className="input-base mt-1"
            placeholder="e.g., 170"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Weight (kg)
          </label>
          <input
            type="number"
            step="0.1"
            value={vitals.weight}
            onChange={(e) => handleChange('weight', e.target.value)}
            className="input-base mt-1"
            placeholder="e.g., 70"
          />
        </div>

        {bmi !== null && (
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              BMI (calculated)
            </label>
            <div className="mt-1 flex h-10 items-center rounded-md border border-gray-300 bg-gray-100 px-3 text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100">
              {bmi.toFixed(1)}
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-end gap-2">
        <button type="submit" className="btn-primary" disabled={createObservation.isPending}>
          {createObservation.isPending ? 'Saving...' : 'Save Vital Signs'}
        </button>
      </div>
    </form>
  );
}
