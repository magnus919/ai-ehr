import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { AllergyList } from '@/components/Allergies/AllergyList';
import { AllergyForm } from '@/components/Allergies/AllergyForm';
import { ErrorBoundary } from '@/components/Common/ErrorBoundary';
import { useUIStore } from '@/store/uiStore';
import { PlusIcon } from '@heroicons/react/24/outline';
import type { AllergyIntolerance } from '@/services/allergies';

export default function AllergiesPage() {
  const [searchParams] = useSearchParams();
  const [selectedPatientId, setSelectedPatientId] = useState<string>(
    searchParams.get('patientId') || ''
  );
  const [selectedAllergy, setSelectedAllergy] = useState<AllergyIntolerance | null>(null);
  const [showForm, setShowForm] = useState(false);

  const setBreadcrumbs = useUIStore((s) => s.setBreadcrumbs);

  useEffect(() => {
    setBreadcrumbs([{ label: 'Allergies' }]);
    return () => setBreadcrumbs([]);
  }, [setBreadcrumbs]);

  const handleEditAllergy = (allergy: AllergyIntolerance) => {
    setSelectedAllergy(allergy);
    setShowForm(true);
  };

  const handleNewAllergy = () => {
    setSelectedAllergy(null);
    setShowForm(true);
  };

  const handleSuccess = () => {
    setShowForm(false);
    setSelectedAllergy(null);
  };

  const handleCancel = () => {
    setShowForm(false);
    setSelectedAllergy(null);
  };

  return (
    <ErrorBoundary section="Allergies">
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Allergies & Intolerances
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Manage patient allergies and intolerances
            </p>
          </div>
          {selectedPatientId && !showForm && (
            <button onClick={handleNewAllergy} className="btn-primary">
              <PlusIcon className="h-4 w-4" />
              Add Allergy
            </button>
          )}
        </div>

        {!selectedPatientId && (
          <div className="card">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Select Patient
            </label>
            <input
              type="text"
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              placeholder="Enter patient ID"
              className="input-base mt-1"
            />
          </div>
        )}

        {selectedPatientId && (
          <>
            {showForm && (
              <AllergyForm
                patientId={selectedPatientId}
                allergy={selectedAllergy || undefined}
                onSuccess={handleSuccess}
                onCancel={handleCancel}
              />
            )}
            <AllergyList patientId={selectedPatientId} onEditAllergy={handleEditAllergy} />
          </>
        )}
      </div>
    </ErrorBoundary>
  );
}
