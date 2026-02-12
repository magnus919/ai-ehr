import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Tab, TabGroup, TabList, TabPanel, TabPanels } from '@headlessui/react';
import {
  PencilSquareIcon,
  PlusIcon,
  PhoneIcon,
  EnvelopeIcon,
  MapPinIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { EncounterList } from '@/components/Encounters/EncounterList';
import {
  usePatient,
  usePatientMedications,
  usePatientConditions,
  usePatientObservations,
} from '@/hooks/usePatients';
import {
  formatName,
  formatDOBWithAge,
  formatPhone,
  formatDate,
} from '@/utils/formatters';
import { GENDER_LABELS } from '@/utils/constants';
import type { UUID } from '@/types';

// -----------------------------------------------------------------------------
// PatientDetail Component
// -----------------------------------------------------------------------------

interface PatientDetailProps {
  patientId: UUID;
}

const tabs = [
  'Overview',
  'Encounters',
  'Medications',
  'Lab Results',
  'Orders',
  'Documents',
];

export function PatientDetail({ patientId }: PatientDetailProps) {
  const navigate = useNavigate();
  const { data: patient, isLoading, error } = usePatient(patientId);
  const [selectedTab, setSelectedTab] = useState(0);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <LoadingSpinner size="lg" label="Loading patient details..." />
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="card text-center" role="alert">
        <h2 className="text-lg font-semibold text-red-800 dark:text-red-200">
          Patient not found
        </h2>
        <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
          The requested patient could not be loaded.
        </p>
        <button
          onClick={() => navigate('/patients')}
          className="btn-primary mt-4"
        >
          Back to Patients
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Patient Header */}
      <div className="card">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          {/* Patient Info */}
          <div className="flex items-start gap-4">
            {/* Avatar */}
            <div className="flex h-16 w-16 flex-shrink-0 items-center justify-center rounded-full bg-primary-100 text-xl font-bold text-primary-700 dark:bg-primary-900 dark:text-primary-300">
              {patient.name.given?.[0]?.charAt(0) ?? '?'}
              {patient.name.family?.charAt(0) ?? '?'}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatName(patient.name)}
                </h1>
                <StatusBadge
                  label={patient.active ? 'Active' : 'Inactive'}
                  color={patient.active ? 'green' : 'gray'}
                  dot
                />
              </div>
              <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500 dark:text-gray-400">
                <span>MRN: <span className="font-mono">{patient.mrn}</span></span>
                <span>{formatDOBWithAge(patient.birthDate)}</span>
                <span>{GENDER_LABELS[patient.gender]}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-2">
            <button
              onClick={() => navigate(`/patients/${patientId}/encounter/new`)}
              className="btn-primary"
            >
              <PlusIcon className="h-4 w-4" />
              New Encounter
            </button>
            <button
              onClick={() => navigate(`/patients/${patientId}/edit`)}
              className="btn-secondary"
            >
              <PencilSquareIcon className="h-4 w-4" />
              Edit
            </button>
          </div>
        </div>

        {/* Contact summary */}
        <div className="mt-4 flex flex-wrap gap-4 border-t border-gray-200 pt-4 text-sm dark:border-gray-700">
          {patient.telecom?.find((t) => t.system === 'phone') && (
            <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
              <PhoneIcon className="h-4 w-4" aria-hidden="true" />
              {formatPhone(
                patient.telecom.find((t) => t.system === 'phone')?.value,
              )}
            </div>
          )}
          {patient.telecom?.find((t) => t.system === 'email') && (
            <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
              <EnvelopeIcon className="h-4 w-4" aria-hidden="true" />
              {patient.telecom.find((t) => t.system === 'email')?.value}
            </div>
          )}
          {patient.address?.[0] && (
            <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
              <MapPinIcon className="h-4 w-4" aria-hidden="true" />
              {[
                patient.address[0].city,
                patient.address[0].state,
              ]
                .filter(Boolean)
                .join(', ')}
            </div>
          )}
          {patient.insurance?.[0] && (
            <div className="flex items-center gap-1 text-gray-600 dark:text-gray-400">
              <ShieldCheckIcon className="h-4 w-4" aria-hidden="true" />
              {patient.insurance[0].provider}
            </div>
          )}
        </div>
      </div>

      {/* Tabbed Content */}
      <TabGroup selectedIndex={selectedTab} onChange={setSelectedTab}>
        <TabList className="flex space-x-1 overflow-x-auto border-b border-gray-200 dark:border-gray-700">
          {tabs.map((tab) => (
            <Tab
              key={tab}
              className={({ selected }) =>
                clsx(
                  'whitespace-nowrap border-b-2 px-4 py-2.5 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500',
                  selected
                    ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200',
                )
              }
            >
              {tab}
            </Tab>
          ))}
        </TabList>

        <TabPanels className="mt-4">
          {/* Overview Tab */}
          <TabPanel>
            <ErrorBoundary section="Patient Overview">
              <PatientOverviewTab patientId={patientId} />
            </ErrorBoundary>
          </TabPanel>

          {/* Encounters Tab */}
          <TabPanel>
            <ErrorBoundary section="Encounters">
              <EncounterList patientId={patientId} />
            </ErrorBoundary>
          </TabPanel>

          {/* Medications Tab */}
          <TabPanel>
            <ErrorBoundary section="Medications">
              <MedicationsTab patientId={patientId} />
            </ErrorBoundary>
          </TabPanel>

          {/* Lab Results Tab */}
          <TabPanel>
            <ErrorBoundary section="Lab Results">
              <LabResultsTab patientId={patientId} />
            </ErrorBoundary>
          </TabPanel>

          {/* Orders Tab */}
          <TabPanel>
            <div className="card">
              <p className="text-sm text-gray-500">
                Patient orders will be displayed here.
              </p>
            </div>
          </TabPanel>

          {/* Documents Tab */}
          <TabPanel>
            <div className="card">
              <p className="text-sm text-gray-500">
                Patient documents will be displayed here.
              </p>
            </div>
          </TabPanel>
        </TabPanels>
      </TabGroup>
    </div>
  );
}

// -----------------------------------------------------------------------------
// Sub-tab Components
// -----------------------------------------------------------------------------

function PatientOverviewTab({ patientId }: { patientId: UUID }) {
  const { data: conditions, isLoading: conditionsLoading } =
    usePatientConditions(patientId);
  const { data: medications, isLoading: medsLoading } =
    usePatientMedications(patientId);

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      {/* Problem List */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white">
          Active Problems
        </h3>
        {conditionsLoading ? (
          <LoadingSpinner className="mt-4" />
        ) : conditions?.length === 0 ? (
          <p className="mt-4 text-sm text-gray-500">No active conditions.</p>
        ) : (
          <ul className="mt-4 divide-y divide-gray-200 dark:divide-gray-700">
            {conditions?.map((condition) => (
              <li key={condition.id} className="py-2">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {condition.code.text ?? condition.code.coding[0]?.display}
                </p>
                <p className="text-xs text-gray-500">
                  {condition.code.coding[0]?.code} &middot;{' '}
                  {formatDate(condition.onsetDateTime)}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Current Medications */}
      <div className="card">
        <h3 className="text-base font-semibold text-gray-900 dark:text-white">
          Current Medications
        </h3>
        {medsLoading ? (
          <LoadingSpinner className="mt-4" />
        ) : medications?.length === 0 ? (
          <p className="mt-4 text-sm text-gray-500">No active medications.</p>
        ) : (
          <ul className="mt-4 divide-y divide-gray-200 dark:divide-gray-700">
            {medications?.map((med) => (
              <li key={med.id} className="py-2">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {med.medicationCodeableConcept.text ??
                    med.medicationCodeableConcept.coding[0]?.display}
                </p>
                <p className="text-xs text-gray-500">
                  {med.dosageInstruction?.[0]?.text ?? 'No dosage specified'}
                </p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function MedicationsTab({ patientId }: { patientId: UUID }) {
  const { data: medications, isLoading } = usePatientMedications(patientId);

  if (isLoading) return <LoadingSpinner className="py-8" />;

  return (
    <div className="card">
      {medications?.length === 0 ? (
        <p className="text-sm text-gray-500">No medications on file.</p>
      ) : (
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead>
            <tr className="table-header">
              <th className="px-4 py-3">Medication</th>
              <th className="px-4 py-3">Dosage</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Prescribed</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {medications?.map((med) => (
              <tr key={med.id}>
                <td className="table-cell font-medium">
                  {med.medicationCodeableConcept.text ??
                    med.medicationCodeableConcept.coding[0]?.display}
                </td>
                <td className="table-cell">
                  {med.dosageInstruction?.[0]?.text ?? '--'}
                </td>
                <td className="table-cell">
                  <StatusBadge
                    label={med.status}
                    color={med.status === 'active' ? 'green' : 'gray'}
                  />
                </td>
                <td className="table-cell">{formatDate(med.authoredOn)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function LabResultsTab({ patientId }: { patientId: UUID }) {
  const { data: observations, isLoading } = usePatientObservations(patientId, {
    category: 'laboratory',
  });

  if (isLoading) return <LoadingSpinner className="py-8" />;

  return (
    <div className="card">
      {observations?.data?.length === 0 ? (
        <p className="text-sm text-gray-500">No lab results on file.</p>
      ) : (
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead>
            <tr className="table-header">
              <th className="px-4 py-3">Test</th>
              <th className="px-4 py-3">Value</th>
              <th className="px-4 py-3">Reference</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Date</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {observations?.data?.map((obs) => (
              <tr key={obs.id}>
                <td className="table-cell font-medium">
                  {obs.code.text ?? obs.code.coding[0]?.display}
                </td>
                <td className="table-cell">
                  {obs.valueQuantity
                    ? `${obs.valueQuantity.value} ${obs.valueQuantity.unit}`
                    : obs.valueString ?? '--'}
                </td>
                <td className="table-cell text-xs text-gray-500">
                  {obs.referenceRange?.[0]?.text ?? '--'}
                </td>
                <td className="table-cell">
                  <StatusBadge
                    label={obs.status}
                    color={obs.status === 'final' ? 'green' : 'blue'}
                  />
                </td>
                <td className="table-cell">
                  {formatDate(obs.effectiveDateTime)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
