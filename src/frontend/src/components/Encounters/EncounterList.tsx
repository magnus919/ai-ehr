import { useNavigate } from 'react-router-dom';
import { ClipboardDocumentListIcon } from '@heroicons/react/24/outline';
import { StatusBadge } from '@/components/Common/StatusBadge';
import { LoadingSpinner } from '@/components/Common/LoadingSpinner';
import { usePatientEncounters } from '@/hooks/usePatients';
import { formatDateTime } from '@/utils/formatters';
import {
  ENCOUNTER_STATUS_LABELS,
  ENCOUNTER_STATUS_COLORS,
  ENCOUNTER_CLASS_LABELS,
} from '@/utils/constants';
import type { UUID, Encounter } from '@/types';

// -----------------------------------------------------------------------------
// EncounterList Component
// -----------------------------------------------------------------------------

interface EncounterListProps {
  patientId: UUID;
}

export function EncounterList({ patientId }: EncounterListProps) {
  const navigate = useNavigate();
  const { data, isLoading } = usePatientEncounters(patientId);

  if (isLoading) {
    return <LoadingSpinner className="py-8" label="Loading encounters..." />;
  }

  const encounters = data?.data ?? [];

  if (encounters.length === 0) {
    return (
      <div className="card flex flex-col items-center py-12">
        <ClipboardDocumentListIcon className="h-12 w-12 text-gray-300 dark:text-gray-600" />
        <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
          No encounters found for this patient.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {encounters.map((encounter) => (
        <EncounterCard
          key={encounter.id}
          encounter={encounter}
          onClick={() => navigate(`/encounters/${encounter.id}`)}
        />
      ))}
    </div>
  );
}

// -----------------------------------------------------------------------------
// EncounterCard Sub-component
// -----------------------------------------------------------------------------

interface EncounterCardProps {
  encounter: Encounter;
  onClick: () => void;
}

function EncounterCard({ encounter, onClick }: EncounterCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="card w-full text-left transition-shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
      aria-label={`View encounter from ${formatDateTime(encounter.period.start)}`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              {ENCOUNTER_CLASS_LABELS[encounter.class] ?? encounter.class} Visit
            </h3>
            <StatusBadge
              label={ENCOUNTER_STATUS_LABELS[encounter.status] ?? encounter.status}
              color={ENCOUNTER_STATUS_COLORS[encounter.status] ?? 'gray'}
              size="sm"
            />
          </div>
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            {formatDateTime(encounter.period.start)}
            {encounter.period.end && ` - ${formatDateTime(encounter.period.end)}`}
          </p>
          {encounter.chiefComplaint && (
            <p className="mt-2 text-sm text-gray-700 dark:text-gray-300">
              <span className="font-medium">Chief Complaint:</span>{' '}
              {encounter.chiefComplaint}
            </p>
          )}
          {encounter.diagnosis && encounter.diagnosis.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {encounter.diagnosis.map((dx, i) => (
                <span
                  key={i}
                  className="badge bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"
                >
                  {dx.condition.display}
                </span>
              ))}
            </div>
          )}
        </div>
        {encounter.participant?.[0]?.individual?.display && (
          <span className="text-xs text-gray-400">
            {encounter.participant[0].individual.display}
          </span>
        )}
      </div>
    </button>
  );
}
