import { useState, useEffect } from 'react';
import { useCreateAllergy, useUpdateAllergy } from '@/hooks/useAllergies';
import type { AllergyIntolerance, AllergyCreate, AllergyUpdate } from '@/services/allergies';

interface AllergyFormProps {
  patientId: string;
  allergy?: AllergyIntolerance;
  onSuccess?: () => void;
  onCancel?: () => void;
}

const ALLERGY_TYPES = [
  { value: 'allergy', label: 'Allergy' },
  { value: 'intolerance', label: 'Intolerance' },
];

const CRITICALITY_OPTIONS = [
  { value: 'low', label: 'Low' },
  { value: 'high', label: 'High' },
  { value: 'unable-to-assess', label: 'Unable to Assess' },
];

const CATEGORY_OPTIONS = [
  'food',
  'medication',
  'environment',
  'biologic',
];

export function AllergyForm({ patientId, allergy, onSuccess, onCancel }: AllergyFormProps) {
  const [formData, setFormData] = useState<AllergyCreate | AllergyUpdate>({
    patient_id: patientId,
    type: allergy?.type || 'allergy',
    category: allergy?.category || [],
    criticality: allergy?.criticality || 'low',
    code: allergy?.code || '',
    code_display: allergy?.code_display || '',
    code_system: allergy?.code_system || 'http://snomed.info/sct',
    onset_datetime: allergy?.onset_datetime || '',
    note: allergy?.note || '',
  });

  const createAllergy = useCreateAllergy();
  const updateAllergy = useUpdateAllergy();

  useEffect(() => {
    if (allergy) {
      setFormData({
        clinical_status: allergy.clinical_status,
        verification_status: allergy.verification_status,
        criticality: allergy.criticality,
        note: allergy.note,
      });
    }
  }, [allergy]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (allergy) {
      await updateAllergy.mutateAsync({
        id: allergy.id,
        input: formData as AllergyUpdate,
      });
    } else {
      await createAllergy.mutateAsync(formData as AllergyCreate);
    }

    if (onSuccess) onSuccess();
  };

  const handleChange = (field: string, value: string | string[]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleCategoryToggle = (category: string) => {
    const currentCategories = (formData as AllergyCreate).category || [];
    const newCategories = currentCategories.includes(category)
      ? currentCategories.filter((c) => c !== category)
      : [...currentCategories, category];
    handleChange('category', newCategories);
  };

  const isEditMode = !!allergy;

  return (
    <form onSubmit={handleSubmit} className="card space-y-6">
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
        {isEditMode ? 'Edit Allergy' : 'Add New Allergy'}
      </h2>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {!isEditMode && (
          <>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Type
              </label>
              <select
                value={(formData as AllergyCreate).type}
                onChange={(e) => handleChange('type', e.target.value)}
                className="input-base mt-1"
                required
              >
                {ALLERGY_TYPES.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Allergen Code
              </label>
              <input
                type="text"
                value={(formData as AllergyCreate).code}
                onChange={(e) => handleChange('code', e.target.value)}
                className="input-base mt-1"
                placeholder="SNOMED CT code"
                required
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Allergen Display Name
              </label>
              <input
                type="text"
                value={(formData as AllergyCreate).code_display}
                onChange={(e) => handleChange('code_display', e.target.value)}
                className="input-base mt-1"
                placeholder="e.g., Peanuts, Penicillin"
                required
              />
            </div>

            <div className="sm:col-span-2">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Categories
              </label>
              <div className="mt-2 flex flex-wrap gap-2">
                {CATEGORY_OPTIONS.map((category) => (
                  <label key={category} className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={((formData as AllergyCreate).category || []).includes(category)}
                      onChange={() => handleCategoryToggle(category)}
                      className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                    />
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                Onset Date (optional)
              </label>
              <input
                type="date"
                value={(formData as AllergyCreate).onset_datetime?.split('T')[0] || ''}
                onChange={(e) => handleChange('onset_datetime', e.target.value ? `${e.target.value}T00:00:00Z` : '')}
                className="input-base mt-1"
              />
            </div>
          </>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Criticality
          </label>
          <select
            value={formData.criticality}
            onChange={(e) => handleChange('criticality', e.target.value)}
            className="input-base mt-1"
          >
            {CRITICALITY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div className="sm:col-span-2">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Notes
          </label>
          <textarea
            value={formData.note || ''}
            onChange={(e) => handleChange('note', e.target.value)}
            rows={3}
            className="input-base mt-1"
            placeholder="Additional notes, reactions, etc."
          />
        </div>
      </div>

      <div className="flex justify-end gap-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary">
            Cancel
          </button>
        )}
        <button
          type="submit"
          className="btn-primary"
          disabled={createAllergy.isPending || updateAllergy.isPending}
        >
          {createAllergy.isPending || updateAllergy.isPending
            ? 'Saving...'
            : isEditMode
            ? 'Update Allergy'
            : 'Add Allergy'}
        </button>
      </div>
    </form>
  );
}
